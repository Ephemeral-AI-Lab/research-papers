import { createHash } from "node:crypto";
import { closeSync, existsSync, lstatSync, openSync, readFileSync, readdirSync, realpathSync, statSync, writeFileSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import { createServer } from "node:net";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import process from "node:process";
import { spawn } from "node:child_process";

const webRoot = resolve(import.meta.dirname, "../../..");
const benchmarkRoot = resolve(webRoot, "..");
const backendRoot = resolve(benchmarkRoot, "backend");
const testRoot = realpathSync(resolve(benchmarkRoot, ".."));
const stateRoot = realpathSync(resolve(testRoot, ".benchmark-state"));
const productRoot = realpathSync(process.env.EOS_PRODUCT_ROOT ?? resolve(testRoot, "../ephemeral-sandbox"));
const productBin = realpathSync(process.env.EOS_PRODUCT_BIN_DIR ?? resolve(productRoot, "target/debug"));
const python = process.env.PYTHON ?? resolve(stateRoot, "test-venv/bin/python");
const stage = process.env.BENCHMARK_REAL_BACKEND_STAGE ?? "full";
const timestamp = new Date().toISOString().replaceAll(":", "-").replaceAll(".", "-");
const requestedEvidence = process.env.BENCHMARK_EVIDENCE_ROOT ?? resolve(stateRoot, "evidence", `real-backend-${stage}-${timestamp}`);
const evidenceRoot = resolve(requestedEvidence);

if (!isAbsolute(requestedEvidence) || !evidenceRoot.startsWith(`${stateRoot}${sep}`)) {
  throw new Error("BENCHMARK_EVIDENCE_ROOT must be an absolute descendant of .benchmark-state");
}
if (!existsSync(python) || !statSync(python).isFile()) throw new Error(`Python runtime is missing: ${python}`);
if (!["small", "medium", "full"].includes(stage)) throw new Error(`Unsupported proof stage: ${stage}`);

await mkdir(dirname(evidenceRoot), { recursive: true });
await mkdir(evidenceRoot, { recursive: false });
const webDist = resolve(evidenceRoot, "web-dist");
const serverLog = resolve(evidenceRoot, "server.log");
const proofFile = resolve(evidenceRoot, "proof-summary.json");
const ignoredSourceDirectories = new Set(["dist", "node_modules", "playwright-report", "test-results", "__pycache__", ".pytest_cache"]);

function run(command, args, options = {}) {
  return new Promise((fulfill, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd ?? webRoot,
      env: options.env ?? process.env,
      stdio: options.stdio ?? "inherit",
    });
    child.once("error", reject);
    child.once("exit", (code, signal) => {
      if (code === 0) fulfill();
      else reject(new Error(`${basename(command)} exited with ${code ?? signal}`));
    });
  });
}

function capture(command, args) {
  return new Promise((fulfill, reject) => {
    const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.once("error", reject);
    child.once("exit", (code) => code === 0 ? fulfill(stdout) : reject(new Error(`${basename(command)} failed: ${stderr.trim()}`)));
  });
}

function sourceDigest() {
  const hash = createHash("sha256");
  function visit(directory) {
    for (const name of readdirSync(directory).sort()) {
      if (ignoredSourceDirectories.has(name)) continue;
      const path = join(directory, name);
      const stat = lstatSync(path);
      if (stat.isSymbolicLink()) throw new Error(`Source contains an unsupported symbolic link: ${path}`);
      if (stat.isDirectory()) visit(path);
      else if (stat.isFile()) {
        hash.update(relative(benchmarkRoot, path));
        hash.update("\0");
        hash.update(readFileSync(path));
        hash.update("\0");
      }
    }
  }
  visit(benchmarkRoot);
  return `sha256:${hash.digest("hex")}`;
}

function directoryEntries(path) {
  return existsSync(path) ? readdirSync(path).sort() : [];
}

async function dockerSnapshot() {
  const [containers, networks, volumes] = await Promise.all([
    capture("docker", ["ps", "-aq"]),
    capture("docker", ["network", "ls", "-q"]),
    capture("docker", ["volume", "ls", "-q"]),
  ]);
  const lines = (value) => value.split("\n").map((item) => item.trim()).filter(Boolean).sort();
  return { containers: lines(containers), networks: lines(networks), volumes: lines(volumes) };
}

async function unusedPort() {
  const server = createServer();
  await new Promise((fulfill, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", fulfill);
  });
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : 0;
  await new Promise((fulfill, reject) => server.close((error) => error ? reject(error) : fulfill()));
  return port;
}

async function ready(origin, server) {
  const deadline = Date.now() + 60_000;
  let last = "no response";
  while (Date.now() < deadline) {
    if (server.exitCode !== null) throw new Error(`Python benchmark service exited with ${server.exitCode}`);
    try {
      const response = await fetch(`${origin}/api/v1/health`, { headers: { Host: new URL(origin).host } });
      const body = await response.json();
      last = JSON.stringify(body);
      if (response.ok && body.execution_ready === true && body.checks?.some(({ id, status }) => id === "execution_backend" && status === "pass")) return body;
    } catch (error) {
      last = String(error);
    }
    await new Promise((fulfill) => setTimeout(fulfill, 100));
  }
  throw new Error(`Python benchmark service did not become ready: ${last}`);
}

async function terminate(child) {
  if (child.exitCode !== null) return;
  const exited = new Promise((fulfill) => child.once("exit", fulfill));
  child.kill("SIGTERM");
  const graceful = await Promise.race([
    exited.then(() => true),
    new Promise((fulfill) => setTimeout(() => fulfill(false), 75_000)),
  ]);
  if (!graceful) {
    child.kill("SIGKILL");
    await exited;
    throw new Error("Python benchmark service exceeded its cleanup deadline");
  }
}

const baseline = {
  source_digest: sourceDigest(),
  runs: directoryEntries(resolve(stateRoot, "runs")),
  runtime: directoryEntries(resolve(stateRoot, "runtime")),
  docker: await dockerSnapshot(),
};
writeFileSync(resolve(evidenceRoot, "baseline.json"), `${JSON.stringify(baseline, null, 2)}\n`);

let server;
let failure;
const startedAt = new Date().toISOString();
try {
  await run(resolve(webRoot, "node_modules/.bin/vite"), ["build", "--outDir", webDist, "--emptyOutDir"], { cwd: webRoot });
  const port = await unusedPort();
  const origin = `http://127.0.0.1:${port}`;
  const logFd = openSync(serverLog, "a");
  server = spawn(python, [
    "-m", "benchmark_lab", "serve",
    "--test-repository-root", testRoot,
    "--product-root", productRoot,
    "--product-bin-dir", productBin,
    "--host", "127.0.0.1",
    "--port", String(port),
    "--web-dist", webDist,
  ], {
    cwd: backendRoot,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
    stdio: ["ignore", logFd, logFd],
  });
  server.once("exit", () => closeSync(logFd));
  await ready(origin, server);
  await run(resolve(webRoot, "node_modules/.bin/playwright"), ["test", "--project=real-backend", "--trace=on"], {
    env: {
      ...process.env,
      BENCHMARK_REAL_BACKEND: "1",
      BENCHMARK_REAL_BACKEND_URL: origin,
      BENCHMARK_REAL_BACKEND_STAGE: stage,
      BENCHMARK_EVIDENCE_ROOT: evidenceRoot,
    },
  });
} catch (error) {
  failure = error;
} finally {
  if (server) {
    try { await terminate(server); }
    catch (error) { failure ??= error; }
  }
}

const final = {
  source_digest: sourceDigest(),
  runs: directoryEntries(resolve(stateRoot, "runs")),
  runtime: directoryEntries(resolve(stateRoot, "runtime")),
  docker: await dockerSnapshot(),
};
const violations = [];
if (final.source_digest !== baseline.source_digest) violations.push("benchmark source changed during the proof");
if (JSON.stringify(final.runs) !== JSON.stringify(baseline.runs)) violations.push("owned run workspaces were not fully removed");
if (JSON.stringify(final.runtime) !== JSON.stringify(baseline.runtime)) violations.push("owned runtime resources were not fully removed");
for (const kind of ["containers", "networks", "volumes"]) {
  const created = final.docker[kind].filter((id) => !baseline.docker[kind].includes(id));
  if (created.length > 0) violations.push(`new Docker ${kind} remain: ${created.join(", ")}`);
}
if (violations.length > 0 && !failure) failure = new Error(violations.join("; "));
writeFileSync(proofFile, `${JSON.stringify({
  schema_version: 1,
  stage,
  started_at: startedAt,
  ended_at: new Date().toISOString(),
  test_repository_root: testRoot,
  product_root: productRoot,
  product_bin_dir: productBin,
  baseline,
  final,
  violations,
  outcome: failure ? "failed" : "passed",
  failure: failure ? String(failure) : null,
}, null, 2)}\n`);
if (failure) throw failure;
