# Documentation claim auditor

This offline static auditor compares documented claims about the checked capability with Python source evidence. It never executes inspected code.

## Usage

```sh
python3 -m pip install .
qr-code-generation-claim-audit audit . --json
python3 -m qr_code_generation_claim_audit audit . --verbose
```

The optional repository path defaults to the current directory. Use `--ignore PREFIX` repeatedly to exclude paths and `--fail-on medium` to include test-only findings. Exit status is 0 for PASS, 2 for findings at the selected threshold, and 1 for usage or I/O errors. Use `--version` to show the version.

The findings are:

```text
documented-qr-code-generation-claim-false
documented-no-qr-code-generation-claim-false
```

## Differentiation

The checked operation encodes data into a two-dimensional matrix. The phrase lists exclude decoding an existing code, producing a one-dimensional strip code, synthesising pictures from content or models, printing marks on paper, and saving a picture without a code leg.

They also exclude spreadsheet reading and generation, word-document reading and generation, presentation reading and generation, PDF extraction, generation, merging, splitting, encryption, rotation, form-filling, watermarking, redaction, compression and annotation, table extraction, OCR, document extraction, e-signature, payment processing, video editing, screen recording and video generation claims.

## Limitations

This phrase may refer to a future roadmap feature:

```text
qr code generation
```

This phrase may refer to a person, web page, or artwork:

```text
qr code generator
```

This phrase may refer to a test fixture or an unshipped sample:

```text
generate qr code
```

This phrase may refer to a Makefile target:

```text
make qr code
```

This phrase may refer to a third-party dashboard:

```text
create qr code
```

This phrase may refer to payload transport:

```text
encode qr code
```

This phrase may refer to displaying an existing code:

```text
render qr code
```

This phrase may refer to the result of a scan:

```text
output qr code
```

- An unrelated object's make method can satisfy the construction pair.
- The pair does not trace whether the method acts on the constructed object.
- A segno make-family call counts even if its result is never saved or shown.
- A qrcodegen encode call counts even if its result is never rendered or saved.
- A pyqrcode create call counts even if its result is never saved or shown.
- A bare library import is not evidence.
- A roadmap, changelog or TODO claim still counts.
- A denial outside the denial list is not recognised and a positive phrase may still count.
- Documents outside the root README and directories named docs are not read.
- Evidence split across modules is missed.
- A locally defined route name shadows the library route, even for a wrapper.
- Dead code counts as evidence.
- Subprocess commands such as qrencode or zint are not evidence.
- A decode call alone is not evidence.
- A one-dimensional barcode operation alone is not evidence.
- A locally defined generic name is shadowed.
- Alias chains the tracer cannot follow are missed.
- Exact phrases are matched without semantic interpretation.
- Implementations in other languages are invisible.
- Runtime-only routes are invisible because code is not executed and the network is not accessed.
- The construction and method legs must be in one module.
- A lone qrcode QRCode construction is not evidence.
- A lone make call without a construction is not evidence.
- A lone make_image call without a construction is not evidence.
- A construction paired only with add_data is not evidence.
- A lone segno QRCode construction is not evidence.
- A lone pyqrcode output method is not evidence.
- A bare name reference is not evidence.
- Strings, comments, filenames and extensions alone are not evidence.
- Syntax-invalid files provide no evidence.
- Image saving alone is not evidence.
- Plotting alone is not evidence.
- Opening or displaying an image alone is not evidence.
- Static matching does not establish whether a detected operation is correct.
