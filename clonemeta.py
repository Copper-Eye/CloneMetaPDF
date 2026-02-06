import os
import sys
import pikepdf

def clone_pdf_attributes(source_pdf_path, target_pdf_path):
    """
    Clones metadata from source_pdf to target_pdf and saves it with a new name.
    """
    if not os.path.exists(source_pdf_path):
        print(f"Error: Source file '{source_pdf_path}' not found.")
        return
    if not os.path.exists(target_pdf_path):
        print(f"Error: Target file '{target_pdf_path}' not found.")
        return

    print(f"Cloning metadata from: {source_pdf_path}")
    print(f"Applying to: {target_pdf_path}")

    # Open both PDFs
    with pikepdf.open(source_pdf_path) as src, pikepdf.open(target_pdf_path) as dst:
        # Capture Producer immediately before pikepdf modifies it (e.g. by accessing XMP)
        src_producer = src.docinfo.get('/Producer')
        
        # 1. Strip existing metadata from target
        for key in list(dst.docinfo.keys()):
            del dst.docinfo[key]

        def copy_value(obj):
            """
            Copies a pikepdf object to the destination.
            Handles indirect objects via copy_foreign.
            Handles direct objects by converting to Python native types where necessary.
            """
            if isinstance(obj, pikepdf.Object) and obj.is_indirect:
                return dst.copy_foreign(obj)
            
            # Direct objects: convert to Python types to create new objects in dst
            if isinstance(obj, pikepdf.String):
                return str(obj)
            elif isinstance(obj, pikepdf.Name):
                return pikepdf.Name(str(obj))
            elif isinstance(obj, pikepdf.Integer):
                return int(obj)
            elif isinstance(obj, pikepdf.Real):
                return float(obj)
            elif isinstance(obj, pikepdf.Boolean):
                return bool(obj)
            elif isinstance(obj, pikepdf.Array):
                return [copy_value(x) for x in obj]
            elif isinstance(obj, pikepdf.Dictionary):
                # Recursively copy dictionary items
                return {k: copy_value(v) for k, v in obj.items()}
            
            # Fallback for unknown types or native python types
            return obj

        # 2. Clone the Document Info dictionary (Title, Author, etc.)
        if src.docinfo:
            for key, value in src.docinfo.items():
                try:
                    dst.docinfo[key] = copy_value(value)
                except Exception as e:
                    print(f"Warning: Could not copy metadata key {key}: {e}")
        
        # 3. Clone/Overwrite XMP metadata
        if '/Metadata' in src.Root:
            with dst.open_metadata() as dst_meta:
                 # Clear existing XMP metadata in target
                for key in list(dst_meta.keys()):
                    del dst_meta[key]
                
                with src.open_metadata() as src_meta:
                    # Copy all XMP entries
                    for key in src_meta:
                        dst_meta[key] = src_meta[key]
        else:
            # Source has no XMP, so remove it from target if present
            if '/Metadata' in dst.Root:
                del dst.Root['/Metadata']

        # 4. Spoof the Producer (Encoding software)
        # pikepdf often appends its version to /Producer unless explicitly set
        if src_producer:
             # Ensure the Producer is strictly copied from source, overwriting any previous setting
             dst.docinfo['/Producer'] = copy_value(src_producer)

        # Determine the new filename based on source name + (edit)
        source_basename = os.path.splitext(os.path.basename(source_pdf_path))[0]
        output_filename = f"{source_basename} (edit).pdf"
        output_path = os.path.join(os.path.dirname(target_pdf_path), output_filename)

        # Save the result
        dst.save(output_path)
        print(f"Successfully saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python clonemeta.py <source_pdf> <target_pdf>")
    else:
        clone_pdf_attributes(sys.argv[1], sys.argv[2])
