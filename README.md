# CloneMetaPDF

A Python utility for transferring PDF document metadata and macOS filesystem metadata from one PDF to another.

CloneMetaPDF uses [pikepdf](https://pikepdf.readthedocs.io/) to copy PDF metadata and Python's built-in `os` module to transfer macOS extended attributes.

The original source and target files are preserved. The resulting PDF is saved as a new file.

## Features

### PDF metadata

- Document Information Dictionary (`/Info`)
- PDF Title
- Author
- Subject
- Keywords
- Creator
- Producer
- Custom Document Info properties
- XMP metadata
- Dublin Core properties
- Custom XMP namespaces
- Nested XMP structures
- Language alternatives and array ordering

By default, document-specific XMP properties are excluded to avoid inheriting misleading identifiers, timestamps and conformance claims.

### macOS metadata

The default configuration copies:

- `com.apple.metadata:kMDItemWhereFroms` — Download origin information
- `com.apple.metadata:kMDItemDownloadedDate` — Download date
- `com.apple.metadata:kMDItemFinderComment` — Finder comments
- `com.apple.metadata:_kMDItemUserTags` — Finder tags

The `--full` option copies all available macOS extended attributes, except `com.apple.quarantine`.

Additional attributes can be specified individually using `--xattr`.

## Requirements

- Python 3.10+
- macOS for extended attribute functionality
- pikepdf 10.0.0 or newer

Install dependencies:

```bash
pip install -r requirements.txt
```

## Project structure

```text
CloneMetaPDF/
│
├── clonemeta.py
├── requirements.txt
└── README.md
```

## Usage

Basic usage:

```bash
python clonemeta.py source.pdf target.pdf
```

The source PDF provides the metadata, which is applied to the target PDF.

The output is saved in the target PDF's directory using the source filename followed by `(edit)`.

Example:

```text
Source: document-1.pdf
Target: document-1-new.pdf

Output: document-1 directory/document-1 (edit).pdf
```

## Command-line options

### Default mode

```bash
python clonemeta.py source.pdf target.pdf
```

Copies the default PDF metadata and selected macOS extended attributes.

### Full macOS metadata

```bash
python clonemeta.py source.pdf target.pdf --full
```

Copies all available extended attributes from the source, excluding:

```text
com.apple.quarantine
```

This can include additional attributes such as Finder information and resource forks.

### Copy all XMP properties

```bash
python clonemeta.py source.pdf target.pdf --all-xmp
```

Includes document-specific XMP properties normally excluded by default, such as:

- `xmp:CreateDate`
- `xmp:ModifyDate`
- `xmp:MetadataDate`
- `xmpMM:DocumentID`
- `xmpMM:InstanceID`
- PDF/A conformance claims

Use this option cautiously. These properties may describe the original PDF rather than the resulting document.

### Full metadata copying

```bash
python clonemeta.py source.pdf target.pdf --full --all-xmp
```

Copies all available macOS extended attributes except quarantine, along with all XMP properties.

### Add individual macOS attributes

```bash
python clonemeta.py source.pdf target.pdf \
    --xattr com.apple.FinderInfo
```

Multiple attributes can be supplied:

```bash
python clonemeta.py source.pdf target.pdf \
    --xattr com.apple.FinderInfo \
    --xattr com.apple.ResourceFork
```

These are added to the default macOS attribute list.

### Overwrite existing output

By default, CloneMetaPDF refuses to overwrite an existing output file.

Use:

```bash
python clonemeta.py source.pdf target.pdf --overwrite
```

## Example commands

Standard copying:

```bash
python clonemeta.py original.pdf replacement.pdf
```

Full macOS attribute copying:

```bash
python clonemeta.py original.pdf replacement.pdf --full
```

Full copying with overwrite:

```bash
python clonemeta.py original.pdf replacement.pdf --full --overwrite
```

Full PDF and macOS metadata copying:

```bash
python clonemeta.py original.pdf replacement.pdf \
    --full \
    --all-xmp \
    --overwrite
```

## Verification

### Inspect PDF metadata

```bash
mdls "original (edit).pdf"
```

### Check download origin

```bash
mdls "original (edit).pdf" | grep -i WhereFroms
```

### Inspect extended attributes

```bash
xattr -l "original (edit).pdf"
```

### Inspect a specific attribute

```bash
xattr -p com.apple.metadata:kMDItemWhereFroms \
    "original (edit).pdf"
```

Note that Spotlight indexing may take some time to update. `xattr` provides a more immediate way to inspect the actual filesystem attributes.

## Important limitations

CloneMetaPDF transfers selected metadata structures, not every possible piece of information contained in a PDF or filesystem.

The following are not guaranteed to be transferred:

- Page-level metadata
- PDF annotations and embedded file metadata
- PDF bookmarks and document structures
- Digital signatures
- Filesystem permissions and ACLs
- Filesystem creation and modification dates
- macOS quarantine information

Saving a modified PDF will generally invalidate existing digital signatures.

Extended attributes are filesystem-level information. They may be lost when a file is emailed, uploaded, downloaded or transferred to a filesystem that does not support them.

The `--full` option may also encounter attributes that macOS does not permit an application to copy. Such failures are reported individually.

## Security considerations

The `com.apple.quarantine` attribute is intentionally excluded, including in full mode.

This prevents the utility from blindly transferring security-related download state and quarantine event information from one file to another.

## Dependencies

Only one external Python dependency is required:

```text
pikepdf>=10.0.0
```

All other functionality uses Python's standard library.

## Licence

Personal use / modify as required.

--full or -full: Copies all macOS extended attributes, except quarantine.
--xattr ATTRIBUTE: Adds individual extended attributes to the default list. Can be repeated.
--all-xmp: Copies all XMP properties, including document-specific identifiers and timestamps.
--overwrite: Allows an existing output file to be overwritten.

The original target PDF is never modified.
The generated output receives metadata from the source PDF.
