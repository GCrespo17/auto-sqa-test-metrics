#!/usr/bin/env python3
"""
Script para obtener pruebas fallidas y no cumplidas de Confluence 
y actualizar Google Sheets.
"""

import os
import json
from dotenv import load_dotenv
from atlassian import Confluence
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

load_dotenv()


def get_confluence_client():
    """Inicializa el cliente de Confluence."""
    return Confluence(
        url=os.environ['CONFLUENCE_URL'],
        username=os.environ['CONFLUENCE_USERNAME'],
        password=os.environ['CONFLUENCE_API_TOKEN']
    )


def get_google_sheets_client():
    """Inicializa el cliente de Google Sheets."""
    credentials_path = os.environ.get('GOOGLE_CREDENTIALS_FILE')
    credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if credentials_path and os.path.exists(credentials_path):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    elif credentials_json:
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    else:
        raise ValueError("Configura GOOGLE_CREDENTIALS_FILE o GOOGLE_CREDENTIALS")
    
    return build('sheets', 'v4', credentials=credentials)


def get_walkthrough_no_cumple(confluence, page_id):
    """
    Obtiene los 'No Cumple' de la página Resultados Walkthrough.
    Retorna el conteo de 'No - No Cumple'.
    """
    page = confluence.get_page_by_id(page_id, expand='body.storage')
    html_content = page['body']['storage']['value']
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    no_cumple_count = 0
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                estado = cells[0].get_text(strip=True).upper()
                cantidad_text = cells[1].get_text(strip=True)
                if 'NO CUMPLE' in estado or 'NO - NO CUMPLE' in estado:
                    try:
                        no_cumple_count = int(cantidad_text)
                    except ValueError:
                        pass
    
    return no_cumple_count


def get_functional_tests_failed(confluence, page_id):
    """
    Obtiene las pruebas FAILED de la página Resultados Pruebas Funcionales.
    Retorna lista de pruebas fallidas y el conteo.
    """
    page = confluence.get_page_by_id(page_id, expand='body.storage')
    html_content = page['body']['storage']['value']
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    failed_tests = []
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                test_case = cells[0].get_text(strip=True)
                status = cells[1].get_text(strip=True).upper()
                
                if status == 'FAILED':
                    failed_tests.append({
                        'test_case': test_case,
                        'status': status,
                        'fecha': cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    })
    
    return failed_tests


def update_google_sheet(sheets_service, spreadsheet_id, cell_range, value):
    """Actualiza una celda específica en Google Sheets."""
    body = {'values': [[value]]}
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=cell_range,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"Google Sheet actualizado: {value} en {cell_range}")


def update_timestamp(sheets_service, spreadsheet_id, cell_range):
    """Actualiza una celda con el timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    body = {'values': [[f"Última actualización: {timestamp}"]]}
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=cell_range,
        valueInputOption='RAW',
        body=body
    ).execute()


def main():
    # Configuración desde variables de entorno
    walkthrough_page_id = os.environ.get('CONFLUENCE_WALKTHROUGH_PAGE_ID')
    functional_page_id = os.environ.get('CONFLUENCE_FUNCTIONAL_PAGE_ID')
    spreadsheet_id = os.environ.get('GOOGLE_SPREADSHEET_ID')
    
    # Celdas para los resultados fallidos (en otra hoja)
    no_cumple_cell = os.environ.get('GOOGLE_DRE_WALK_CELL', 'DRE!B2')
    failed_cell = os.environ.get('GOOGLE_DRE_FUNCTIONAL_CELL', 'Fallidos!A2')
    timestamp_cell = os.environ.get('GOOGLE_FAILED_TIMESTAMP_CELL', 'Fallidos!A3')
    
    if not walkthrough_page_id:
        raise ValueError("CONFLUENCE_WALKTHROUGH_PAGE_ID no está configurado")
    
    if not functional_page_id:
        raise ValueError("CONFLUENCE_FUNCTIONAL_PAGE_ID no está configurado")
    
    if not spreadsheet_id:
        raise ValueError("GOOGLE_SPREADSHEET_ID no está configurado")
    
    # Conectar a Confluence y Google Sheets
    confluence = get_confluence_client()
    sheets_service = get_google_sheets_client()
    
    # Obtener No Cumple del Walkthrough
    no_cumple_count = get_walkthrough_no_cumple(confluence, walkthrough_page_id)
    print(f"Walkthrough - No Cumple: {no_cumple_count}")
    
    # Obtener pruebas fallidas de Funcionales
    failed_tests = get_functional_tests_failed(confluence, functional_page_id)
    failed_count = len(failed_tests)
    print(f"Pruebas Funcionales- Failed: {failed_count}")
    for test in failed_tests:
        print(f"  - {test['test_case']}")
    
    # Actualizar Google Sheet
    update_google_sheet(sheets_service, spreadsheet_id, no_cumple_cell, no_cumple_count)
    update_google_sheet(sheets_service, spreadsheet_id, failed_cell, failed_count)
    
    return {'no_cumple': no_cumple_count, 'failed': failed_count}


if __name__ == '__main__':
    main()
