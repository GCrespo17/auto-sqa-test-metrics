#!/usr/bin/env python3
"""
Script para obtener pruebas exitosas de Confluence y actualizar Google Sheets.
Ejecutado automáticamente cada 2 horas via GitHub Actions.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()
from atlassian import Confluence
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime


def get_confluence_client():
    """Inicializa el cliente de Confluence."""
    return Confluence(
        url=os.environ['CONFLUENCE_URL'],
        username=os.environ['CONFLUENCE_USERNAME'],
        password=os.environ['CONFLUENCE_API_TOKEN']
    )


def get_google_sheets_client():
    """Inicializa el cliente de Google Sheets usando credenciales de servicio."""
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


def get_test_results_from_confluence(confluence, page_id):
    """
    Obtiene los resultados de pruebas desde una página de Confluence.
    Retorna lista de pruebas exitosas (PASSED).
    """
    page = confluence.get_page_by_id(page_id, expand='body.storage')
    html_content = page['body']['storage']['value']
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    passed_tests = []
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:  # Saltar header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                test_case = cells[0].get_text(strip=True)
                status = cells[1].get_text(strip=True).upper()
                
                if status == 'PASSED':
                    passed_tests.append({
                        'test_case': test_case,
                        'status': status,
                        'fecha': cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    })
    
    return passed_tests


def update_google_sheet(sheets_service, spreadsheet_id, cell_range, count):
    """
    Actualiza una celda específica en Google Sheets con el conteo de pruebas.
    """
    body = {
        'values': [[count]]
    }
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=cell_range,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"Google Sheet actualizado: {count} pruebas exitosas en {cell_range}")


def update_timestamp(sheets_service, spreadsheet_id, cell_range):
    """Actualiza una celda con el timestamp de última ejecución."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    body = {
        'values': [[f"Última actualización: {timestamp}"]]
    }
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=cell_range,
        valueInputOption='RAW',
        body=body
    ).execute()


def main():
    # Configuración desde variables de entorno
    confluence_page_id = os.environ.get('CONFLUENCE_PAGE_ID')
    spreadsheet_id = os.environ.get('GOOGLE_SPREADSHEET_ID')
    cell_range = os.environ.get('GOOGLE_CELL_RANGE', 'Hoja1!B2')
    timestamp_cell = os.environ.get('GOOGLE_TIMESTAMP_CELL', 'Hoja1!A1')
    
    if not confluence_page_id:
        raise ValueError("CONFLUENCE_PAGE_ID no está configurado")
    
    if not spreadsheet_id:
        raise ValueError("GOOGLE_SPREADSHEET_ID no está configurado")
    
    # Conectar a Confluence
    confluence = get_confluence_client()
    
    # Conectar a Google Sheets
    sheets_service = get_google_sheets_client()
    
    # Obtener pruebas exitosas
    passed_tests = get_test_results_from_confluence(confluence, confluence_page_id)
    passed_count = len(passed_tests)
    
    print(f"Pruebas exitosas encontradas: {passed_count}")
    for test in passed_tests:
        print(f"  - {test['test_case']}")
    
    # Actualizar Google Sheet
    update_google_sheet(sheets_service, spreadsheet_id, cell_range, passed_count)
    return passed_count



if __name__ == '__main__':
    main()
