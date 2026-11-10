
#!/usr/bin/env python3

import os
import sys
import argparse
import pikepdf
import xattr

DEFAULT_MACOS_ATTRIBUTES = [
    "com.apple.metadata:kMDItemWhereFroms",
    "com.apple.metadata:kMDItemDownloadedDate",
    "com.apple.metadata:kMDItemFinderComment",
    "com.apple.metadata:_kMDItemUserTags",
]

EXCLUDED_MACOS_ATTRIBUTES = {
    "com.apple.quarantine",
}

DEFAULT_EXCLUDED_XMP = {
    "xmp:CreateDate",
    "xmp:ModifyDate",
    "xmp:MetadataDate",
    "pdf:Producer",
    "xmpMM:DocumentID",
    "xmpMM:InstanceID",
    "pdfaid:part",
    "pdfaid:conformance",
}

def copy_macos_metadata(
    source,
    destination,
    full=False,
    extra_attributes=None
):

    print("\n===== MACOS EXTENDED ATTRIBUTES =====")
    excluded = {"com.apple.quarantine"}
    default_attributes = {
        "com.apple.metadata:kMDItemWhereFroms",
        "com.apple.metadata:kMDItemDownloadedDate",
        "com.apple.metadata:kMDItemFinderComment",
        "com.apple.metadata:_kMDItemUserTags",
    }
    extra_attributes = set(extra_attributes or [])
    src_attrs = xattr.xattr(source)
    dst_attrs = xattr.xattr(destination)
    source_attributes = set(src_attrs.keys())

    if full:
        attributes = source_attributes
        print("FULL MODE: copying all extended attributes.")
    else:
        attributes = default_attributes
    attributes.update(extra_attributes)
    attributes -= excluded
    if full:
        for attribute in list(dst_attrs.keys()):
            if attribute not in excluded:
                try:
                    del dst_attrs[attribute]
                except OSError as e:
                    print(f"Could not remove {attribute}: {e}")

    copied = 0
    skipped = 0
    failed = 0

    for attribute in sorted(attributes):
        if attribute not in source_attributes:
            skipped += 1
            continue
        try:
            dst_attrs[attribute] = src_attrs[attribute]
            print(f"Copied: {attribute}")
            copied += 1
        except Exception as e:
            print(f"Failed: {attribute}: {e}")
            failed += 1

    print("\nMACOS ATTRIBUTE SUMMARY")
    print(f"Copied:  {copied}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")

def copy_pdf_metadata(
    source,
    target,
    output,
    all_xmp=False
):

    print("\n===== PDF METADATA =====")
    excluded_xmp = (
        set() if all_xmp else DEFAULT_EXCLUDED_XMP
    )
    with (
        pikepdf.open(source) as src,
        pikepdf.open(target) as dst
    ):
        if "/Info" in src.trailer:
            dst.trailer["/Info"] = dst.copy_foreign(
                src.trailer["/Info"]
            )
            print("Document Info dictionary copied.")
        else:
            if "/Info" in dst.trailer:
                del dst.trailer["/Info"]
            print("Source has no Document Info dictionary.")
        if "/Metadata" in src.Root:
            with (
                src.open_metadata(
                    set_pikepdf_as_editor=False,
                    update_docinfo=False
                ) as src_meta,

                dst.open_metadata(
                    set_pikepdf_as_editor=False,
                    update_docinfo=False
                ) as dst_meta
            ):

                for key in list(dst_meta):
                    del dst_meta[key]
                copied = dst_meta.copy_properties(
                    src_meta,
                    list(src_meta),
                    exclude=excluded_xmp,
                    overwrite=True
                )

                print(f"XMP properties copied: {len(copied)}")

                if excluded_xmp:
                    excluded_found = (
                        excluded_xmp.intersection(src_meta.keys())
                    )
                    if excluded_found:
                        print("Excluded document-specific properties:")
                        for key in sorted(excluded_found):
                            print(f"  - {key}")

        else:
            if "/Metadata" in dst.Root:
                del dst.Root["/Metadata"]
            print("Source has no XMP metadata.")

        dst.save(
            output,
            fix_metadata_version=False
        )

    print("PDF metadata saved successfully.")

def clone_pdf_attributes(
    source_pdf_path,
    target_pdf_path,
    full=False,
    extra_attributes=None,
    all_xmp=False,
    overwrite=False
):

    source_pdf_path = os.path.abspath(source_pdf_path)
    target_pdf_path = os.path.abspath(target_pdf_path)

    if not os.path.isfile(source_pdf_path):
        raise FileNotFoundError(
            f"Source PDF not found: {source_pdf_path}"
        )

    if not os.path.isfile(target_pdf_path):
        raise FileNotFoundError(
            f"Target PDF not found: {target_pdf_path}"
        )

    if os.path.samefile(source_pdf_path, target_pdf_path):
        raise ValueError(
            "Source and target must be different files."
        )

    source_basename = os.path.splitext(
        os.path.basename(source_pdf_path)
    )[0]

    output_filename = f"{source_basename} (edit).pdf"

    output_path = os.path.join(
        os.path.dirname(target_pdf_path),
        output_filename
    )

    if os.path.abspath(output_path) in (
        source_pdf_path,
        target_pdf_path
    ):
        raise ValueError(
            "Output path conflicts with source or target."
        )

    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(
            f"Output already exists: {output_path}\n"
            "Use --overwrite to replace it."
        )

    print("=" * 60)
    print("                 PDF METADATA CLONER")
    print("=" * 60)
    print(f"\nSource: {source_pdf_path}")
    print(f"Target: {target_pdf_path}")
    print(f"Output: {output_path}")
    print(f"\nFull macOS attributes: {full}")
    print(f"All XMP properties:    {all_xmp}")

    copy_pdf_metadata(
        source_pdf_path,
        target_pdf_path,
        output_path,
        all_xmp=all_xmp
    )

    copy_macos_metadata(
        source_pdf_path,
        output_path,
        full=full,
        extra_attributes=extra_attributes
    )

    print("\n" + "=" * 60)
    print("METADATA COPYING COMPLETE")
    print("=" * 60)
    print(f"\nOutput:\n{output_path}")
    return output_path

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Clone PDF metadata and macOS extended "
            "attributes from one PDF to another."
        )
    )

    parser.add_argument(
        "source",
        help="Source PDF containing the metadata."
    )

    parser.add_argument(
        "target",
        help="Target PDF receiving the metadata."
    )

    parser.add_argument(
        "-full",
        "--full",
        action="store_true",
        help=(
            "Copy all macOS extended attributes "
            "except com.apple.quarantine."
        )
    )

    parser.add_argument(
        "--xattr",
        action="append",
        default=[],
        metavar="ATTRIBUTE",
        help=(
            "Add a specific macOS extended attribute "
            "to the default copying list. Can be repeated."
        )
    )

    parser.add_argument(
        "--all-xmp",
        action="store_true",
        help=(
            "Copy all XMP properties, including "
            "document-specific identifiers and timestamps."
        )
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing output PDF."
    )

    args = parser.parse_args()

    try:
        clone_pdf_attributes(
            source_pdf_path=args.source,
            target_pdf_path=args.target,
            full=args.full,
            extra_attributes=args.xattr,
            all_xmp=args.all_xmp,
            overwrite=args.overwrite
        )
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
