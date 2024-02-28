from .post_processor_interface import PostProcessorInterface
import pypandoc
import tempfile
import os

class EBookPostProcessor(PostProcessorInterface):
    @staticmethod
    def process(content, output_filename):
        # Create a temporary file to save the markdown content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as md_temp:
            md_temp_path = md_temp.name
            md_temp.write(content)
            md_temp.flush()
        
        try:
            # Convert the markdown content to a PDF ebook using pandoc
            # and save it to the specified output filename
            pypandoc.convert_file(md_temp_path, 'pdf', outputfile='output/' + output_filename)
        finally:
            # Clean up the temporary markdown file
            os.unlink(md_temp_path)

        # Return the path to the saved PDF file
        return f"eBook saved to: {output_filename}"
