import os
from docx import Document
from fpdf import FPDF
import app_config as config

def save_text_to_word(text_content: str, output_filepath: str, status_callback=None) -> bool:
    if not output_filepath.lower().endswith(".docx"):
        output_filepath += ".docx"
        if status_callback:
            status_callback(f"Warning: Appended '.docx' to output filepath: {output_filepath}")

    try:
        if status_callback:
            status_callback(f"Creating Word document: {os.path.basename(output_filepath)}...")

        document = Document()
        for para_text in text_content.splitlines():
            document.add_paragraph(para_text if para_text.strip() else "")

        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            if status_callback:
                status_callback(f"Created output directory: {output_dir}")

        document.save(output_filepath)
        if status_callback:
            status_callback(f"Word document saved successfully: {output_filepath}")
        print(f"Word document saved successfully: {output_filepath}")
        return True
    except Exception as e:
        error_msg = f"Error saving Word document '{os.path.basename(output_filepath)}': {e}"
        if status_callback:
            status_callback(error_msg)
        print(error_msg)
        return False

class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.font_path_regular = config.POPPINS_REGULAR_PATH
        self.font_path_bold = config.POPPINS_BOLD_PATH
        self.font_family_name = "CustomFont"
        self.setup_fonts()

    def setup_fonts(self):
        try:
            dejavu_font_path = os.path.join(config.FONTS_DIR, "DejaVuSans.ttf")
            if os.path.exists(dejavu_font_path):
                self.add_font("DejaVu", "", dejavu_font_path, uni=True)
                self.font_family_name = "DejaVu"
                return
        except Exception as e:
            print(f"Could not load DejaVuSans font: {e}. Trying Poppins.")

        try:
            if os.path.exists(self.font_path_regular):
                self.add_font(self.font_family_name, "", self.font_path_regular, uni=True)
                if os.path.exists(self.font_path_bold):
                    self.add_font(self.font_family_name, "B", self.font_path_bold, uni=True)
            else:
                raise FileNotFoundError(f"{self.font_path_regular} not found.")
        except Exception as e:
            print(f"Could not load custom font ({self.font_path_regular}): {e}. Falling back to Arial.")
            self.font_family_name = "Arial"

    def chapter_body(self, text_content):
        self.set_font(self.font_family_name, size=11)
        for line in text_content.replace('\r\n', '\n').split('\n'):
            self.multi_cell(0, 5, line)

def save_text_to_pdf(text_content: str, output_filepath: str, status_callback=None) -> bool:
    if not output_filepath.lower().endswith(".pdf"):
        output_filepath += ".pdf"
        if status_callback:
            status_callback(f"Warning: Appended '.pdf' to output filepath: {output_filepath}")

    try:
        if status_callback:
            status_callback(f"Creating PDF document: {os.path.basename(output_filepath)}...")

        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()

        if status_callback:
            status_callback(f"PDF will use font: {pdf.font_family_name}")

        pdf.chapter_body(text_content)

        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            if status_callback:
                status_callback(f"Created output directory: {output_dir}")

        pdf.output(output_filepath, "F")
        if status_callback:
            status_callback(f"PDF document saved successfully: {output_filepath}")
        print(f"PDF document saved successfully: {output_filepath}")
        return True
    except Exception as e:
        error_msg = f"Error saving PDF document '{os.path.basename(output_filepath)}': {e}"
        if status_callback:
            status_callback(error_msg)
        print(error_msg)
        return False
