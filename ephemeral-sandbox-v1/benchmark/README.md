# EphemeralOS benchmark laboratory

This is the external Python benchmark implementation for EphemeralOS. It uses three explicit canonical roots: the test repository, the product repository, and a directory of prebuilt product executables. Benchmark source is read-only at runtime; all mutable state lives under `<TEST_REPOSITORY_ROOT>/.benchmark-state`.

Install the Python package and web dependencies in controlled environments, then build the web application into owned state:

```sh
cd <TEST_REPOSITORY_ROOT>/benchmark/web
npm ci
npm run build -- --outDir <TEST_REPOSITORY_ROOT>/.benchmark-state/web-dist --emptyOutDir
```

Run the application from any current directory with canonical absolute roots and prebuilt product executables:

```sh
sandbox-benchmark serve \
  --test-repository-root <TEST_REPOSITORY_ROOT> \
  --product-root <PRODUCT_ROOT> \
  --product-bin-dir <PRODUCT_BIN_DIR>
```

The CLI and API share one campaign runner. `pytest` verifies the application and is not used as the scheduler. Migration authority and retained phase evidence are tracked in `MIGRATION_CHECKLIST.md`.
