"""This module is responsible for interactions with the SAP UI."""

import os
from datetime import datetime, timedelta
import uuid

import uiautomation
from itk_dev_shared_components.sap import multi_session

FINE_RATES = (
    (datetime(2024, 1, 1), 945),
    (datetime(2023, 1, 1), 900),
    (datetime(2023, 1, 1), 580),
    (datetime(2022, 1, 1), 570),
    (datetime(2021, 1, 1), 560),
    (datetime(2020, 1, 1), 550),
    (datetime(1900, 1, 1), 500)
)


def get_sap_session():
    """Get the first open session of SAP."""
    return multi_session.get_all_sap_sessions()[0]


def get_fine_rate(fine_date: datetime) -> int:
    """Find the fine rate at a given date using the fine rate table in the configs.

    Args:
        fine_date: The date to find the fine rate for.

    Raises:
        ValueError: If no rate could be found for the date.

    Returns:
        The fine rate for the given date.
    """
    for rate_date, value in FINE_RATES:
        if fine_date >= rate_date:
            return value
    raise ValueError(f"No fine rate could be found for the date: {fine_date}")


def create_invoice(cpr: str, move_date: datetime, register_date: datetime, to_address: str):
    """Create an invoice with the given parameters.

    Args:
        session: The SAP session.
        cpr: The cpr number of the person to receive the invoice.
        move_date: The date the person moved.
        register_date: The date the person registered their move.
        to_address: The address the person moved to.

    Raises:
        RuntimeError: If the invoice can't be created.
    """
    session = get_sap_session()

    # Start session
    session.startTransaction("ZDKD_OPRET_FAKTURA")

    # Fill out first form
    session.findById("wnd[0]/usr/ctxtLV_BP_IN").text = cpr
    session.findById("wnd[0]/usr/ctxtP_IHS_IN").text = "FKRB"
    session.findById("wnd[0]/usr/txtP_NBS_IN").text = cpr
    session.findById("wnd[0]/tbar[1]/btn[8]").press()

    # Fill out second form
    session.findById("wnd[0]/usr/ctxtZDKD0312MODTAGKRAV_UDVEKSLE-FORFALDSDATO").text = register_date.strftime("%d.%m.%Y")
    session.findById("wnd[0]/usr/txtZDKD0313BETALINGSSPEC_UDVEKSLE-TEKSTLINIE1").text = "Folkeregisterbøde - CPR-lovens §§ 57-58"
    session.findById("wnd[0]/usr/txtZDKD0313BETALINGSSPEC_UDVEKSLE-TEKSTLINIE2").text = f'For sent anmeldt flytning {register_date.strftime("%d.%m.%Y")}'
    session.findById("wnd[0]/usr/txtZDKD0313BETALINGSSPEC_UDVEKSLE-TEKSTLINIE3").text = f'til {to_address}'

    # Fill out invoice lines
    fine_rate = get_fine_rate(move_date + timedelta(days=6))
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/txtWA_FAKTURALINIE-BELOEB[4,0]").text = fine_rate

    date_string = (move_date + timedelta(days=14)).strftime("%d.%m.%Y")
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-LINJE_PERIODE_FRA[6,0]").text = date_string
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-LINJE_PERIODE_TIL[7,0]").text = date_string
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-STIFTELSESDATO[13,0]").text = date_string

    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-VALOERDATO[15,0]").text = datetime.today().strftime("%d.%m.%Y")
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-HOVED_TRANS[9,0]").text = "FKRB"
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-DEL_TRANS[10,0]").text = "FK01"
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-FORDRING_TYPE[16,0]").text = "KFFORBØ"
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-BETALINGS_MODT_KODE[18,0]").text = "02"
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/txtWA_FAKTURALINIE-BETALINGS_MODT[19,0]").text = cpr
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/ctxtWA_FAKTURALINIE-YDELSES_MODT_KODE[20,0]").text = "02"
    session.findById("wnd[0]/usr/tblSAPLZDKD0068_MODTAGKRAVDIAFAKTLINJECTR/txtWA_FAKTURALINIE-YDELSES_MODT[21,0]").text = cpr

    # Save
    session.findById("wnd[0]/tbar[0]/btn[11]").press()

    # Check for success popup
    if session.FindById("wnd[1]/usr/txtMESSTXT1").text != 'Krav(ene) blev oprettet.':
        raise RuntimeError(f"Couldn't create invoice: {cpr=} {move_date=} {register_date=} {to_address=}")

    # Dismiss popup and go back
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    session.findById("wnd[0]/tbar[0]/btn[3]").press()


def do_immediate_invoicing(cpr: str):
    """Perform immediate invocing on the person with the given cpr.

    Args:
        session: The SAP session.
        cpr: The cpr number to perform immediate invoicing on.

    Raises:
        RuntimeError: If the right account can't be found.
    """
    session = get_sap_session()

    session.startTransaction("FKKINV_S")
    session.findById("wnd[0]/usr/ctxtINV_PR").text = "IF"  # TODO: Change back to FI
    session.findById("wnd[0]/usr/ctxtPARTNER").text = cpr
    session.findById("wnd[0]/tbar[1]/btn[8]").press()

    # Select account
    table = session.findById("wnd[1]/usr/tblSAPLFKKGACCOUNT")
    for i in range(table.RowCount):
        cell = table.getCell(i, 1)
        if cell.text == 'Magistratsafdelingen - MKB':
            cell.setFocus()
            session.findById("wnd[1]/tbar[0]/btn[0]").press()
            break
    else:
        raise RuntimeError("Couldn't find the account 'Magistratsafdelingen - MKB'.")

    # Select all and accept
    session.findById("wnd[1]/tbar[0]/btn[5]").press()
    session.findById("wnd[1]/tbar[0]/btn[8]").press()

    # A popup might appear if multiple invoices are pending
    if session.findById("wnd[1]").text == 'Opbygning af faktureringsenheder':
        # Select all and select
        session.findById("wnd[1]/tbar[0]/btn[19]").press()
        session.findById("wnd[1]/tbar[0]/btn[8]").press()

    # Press yes
    session.findById("wnd[1]/usr/btnBUTTON_1").press()

    # Press ok
    session.findById("wnd[1]/tbar[0]/btn[0]").press()

    # Go back
    session.findById("wnd[0]/tbar[0]/btn[3]").press()


def save_invoice(cpr: str, invoice_date: datetime) -> str:
    """Find the invoice on the given cpr with the given date
    and save it as a pdf.

    Args:
        session: The SAP session.
        cpr: The cpr number of the person with the invoice.
        invoice_date: The date of the invoice.

    Raises:
        ValueError: If the invoice couldn't be found.

    Returns:
        The file path of the invoice pdf.
    """
    session = get_sap_session()

    session.startTransaction("fmcacov")

    # Search for person
    session.findById("wnd[0]/usr/ctxtGPART_DYN").text = cpr
    session.findById("wnd[0]").sendVKey(0)

    # Find invoice by date and description
    session.findById("wnd[0]/usr/tabsDATA_DISP/tabpDATA_DISP_FC3").select()
    table = session.findById("wnd[0]/usr/tabsDATA_DISP/tabpDATA_DISP_FC3/ssubDATA_DISP_SCA:RFMCA_COV:0204/cntlRFMCA_COV_0100_CONT3/shellcont/shell")
    for row in range(table.RowCount):
        if table.GetCellValue(row, "DATE") == invoice_date.strftime("%d.%m.%Y") and table.GetCellValue(row, "ZZ_KONTAKTRELATION").startswith("FKRB"):
            break
    else:
        raise ValueError("Couldn't find an invoice on the invoice date.")

    # Open the document
    table.setCurrentCell(row, "DATE")
    table.contextMenu()
    table.selectContextMenuItem("VIS_ODA_CON")
    session.findById("wnd[0]/usr/cntlCONT1/shellcont/shell").currentCellColumn = "PRINT_OWNER_ID"
    session.findById("wnd[0]/usr/cntlCONT1/shellcont/shell").doubleClickCurrentCell()

    # Go back to home screen
    session.findById("wnd[0]/tbar[0]/btn[12]").press()
    session.findById("wnd[0]/tbar[0]/btn[12]").press()

    return _save_invoice_file()


def _save_invoice_file() -> str:
    """Find the Microsoft Edge window with the invoice pdf open
    and save the document. Close Edge afterwards.

    Returns:
        The path of the saved document.
    """
    file_path = os.path.join(os.getcwd(), f"invoice {uuid.uuid4()}.pdf")

    uiautomation.PaneControl(Name="Faktura – Microsoft Edge", searchDepth=2).SendKeys("{ctrl}s")
    file_dialog = uiautomation.WindowControl(Name="Gem som", searchDepth=2)
    file_dialog.PaneControl(AutomationId="BackgroundClear", searchDepth=4).EditControl(AutomationId="1001").GetValuePattern().SetValue(file_path)
    file_dialog.ButtonControl(Name="Gem", searchDepth=1).GetInvokePattern().Invoke()

    return file_path


if __name__ == '__main__':
    create_invoice("8412893981", datetime(2024, 6, 1), datetime(2024, 6, 20), "Hejvej 2, 7894 Hejby")
    do_immediate_invoicing("8412893981")
