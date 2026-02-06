# PDF Metadata Cloner

A Python utility to clone all metadata (Info dictionary, XMP, dates, and Producer) from one PDF file to another.

## Features

- **Exact Metadata Cloning**: Copies `/Title`, `/Author`, `/Subject`, `/Keywords`, dates, and more.
- **XMP Support**: Mirrors XMP metadata hierarchy.
- **Strict Mirroring**: strips all existing metadata from the target file relative to the source (prevents "ghost" tags).
- **Producer Spoofing**: Forcefully copies the `Producer` (Encoding Software) field, preventing libraries like `pikepdf` from adding their own signatures.
- **Safe Output**: Saves the result as `[Source Name] (edit).pdf` to avoid overwriting files.

## Installation

1. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python clonemeta.py <source_pdf> <target_pdf>
```

### Example

```bash
python clonemeta.py "reference_doc.pdf" "my_new_doc.pdf"
```
This will create `reference_doc (edit).pdf` containing the content of `my_new_doc.pdf` looking exactly like `reference_doc.pdf` in terms of metadata properties.

## Testing

To run the comprehensive test suite:

```bash
python -m unittest discover tests
```

## How It Works

1. **Strips** the target PDF of all existing `/Info` and XMP metadata.
2. **Copies** the full `/Info` dictionary from source to target.
3. **Copies** the XMP packet (if present in source).
4. **Resets** the `/Producer` field to match the source exactly, bypassing standard library behavior that tries to watermark the file.
