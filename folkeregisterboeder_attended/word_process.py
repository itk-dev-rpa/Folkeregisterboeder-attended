"""This module handles generating Word files from templates."""

import zipfile
import os
import shutil
from datetime import date, timedelta, datetime

from folkeregisterboeder_attended.task import Task
from folkeregisterboeder_attended import sap_process


def create_letter(task: Task, address_lines: list[str]):
    """Generate a letter from the letter template from a given task and
    address.

    Args:
        task: The task to create the letter from.
        address_lines: The receiver address to insert into the letter.

    Returns:
        The file path of the generated letter.
    """
    template_path = r"folkeregisterboeder_attended\docs\Din flytning er anmeldt for sent.docx"
    result_path = "letter.docx"

    fine_rate = sap_process.get_fine_rate(task.move_date + timedelta(days=6))

    keywords_replacements = {
        "SENDEDATO": format_date(datetime.today()),
        "ANMELDELSESDATO": format_date(task.register_date),
        "FLYTTEDATO": format_date(task.move_date),
        "ADRESSE1": address_lines[0],
        "ADRESSE2": address_lines[1],
        "ADRESSE3": address_lines[2],
        "ADRESSE4": address_lines[3],
        "ADRESSE5": address_lines[4],
        "FLYTTE_ADRESSE": task.address,
        "BELØB": str(fine_rate),
        "SAGSNUMMER": task.nova_case_number
    }

    replace_keywords_in_word_template(template_path, result_path, keywords_replacements)

    return result_path


def replace_keywords_in_word_template(template_path: str, result_path: str, keywords_replacements: dict[str, str]):
    """Insert text into a word template.

    Args:
        template_path: The file path of the word template file.
        result_path: The file path of the resulting word file.
        keywords_replacements: A dictionary with template keywords and the text to insert.
    """
    # Create a temporary directory to extract the files
    temp_dir = "temp_zip_extraction"
    os.makedirs(temp_dir, exist_ok=True)

    # Extract all files from the zip archive
    with zipfile.ZipFile(template_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Iterate through all extracted files
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".xml"):  # Consider only xml files
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf-8") as f:
                    content = f.read()
                # Replace keywords with replacements
                for keyword, replacement in keywords_replacements.items():
                    content = content.replace(keyword, replacement)
                # Write modified content back to the file
                with open(file_path, 'w', encoding="utf-8") as f:
                    f.write(content)

    # Re-zip the modified files
    with zipfile.ZipFile(result_path, 'w') as zip_ref:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                zip_ref.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)


def format_date(in_date: date) -> str:
    """Format a date object as a danish date string.
    E.g. date(2024, 1, 1) -> 1. januar 2024

    Args:
        in_date: The date object to format.

    Returns:
        A danish string representation of the date.
    """
    months = ("januar", "februar", "marts", "april", "maj", "juni", "juli", "august", "september", "oktober", "november", "december")
    return f"{in_date.day}. {months[in_date.month-1]} {in_date.year}"
