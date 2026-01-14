# Automatización Confluence → Google Sheets

Este proyecto automatiza la extracción de datos de pruebas desde Confluence y los actualiza en Google Sheets.

## Configuración

### 1. Secrets de GitHub

Ve a **Settings → Secrets and variables → Actions** en tu repositorio y agrega estos secrets:

| Secret | Descripción |
|--------|-------------|
| `CONFLUENCE_URL` | URL de tu instancia de Confluence (ej: `https://tuempresa.atlassian.net`) |
| `CONFLUENCE_USERNAME` | Tu email de Atlassian |
| `CONFLUENCE_API_TOKEN` | [API Token de Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `CONFLUENCE_FUNCTIONAL_PAGE_ID` | ID de la página de Resultados Funcionales |
| `CONFLUENCE_WALKTHROUGH_PAGE_ID` | ID de la página de Resultados Walkthrough |
| `GOOGLE_SPREADSHEET_ID` | ID del spreadsheet (está en la URL) |
| `GOOGLE_CREDENTIALS` | JSON completo de la cuenta de servicio de Google |
| `GOOGLE_FUNCTIONAL_PAGE_CELL_RANGE` | Celda para pruebas exitosas (ej: `Funcionales!A2`) |
| `GOOGLE_DRE_WALK_CELL` | Celda para No Cumple walkthrough (ej: `DRE!B2`) |
| `GOOGLE_DRE_FUNCTIONAL_CELL` | Celda para pruebas fallidas (ej: `Fallidos!A2`) |

### 2. Configurar cronjob.org

1. Crea una cuenta en [cronjob.org](https://cronjob.org)

2. Crea un nuevo cronjob con esta URL:
   ```
   https://api.github.com/repos/TU_USUARIO/TU_REPO/dispatches
   ```

3. Configura el método como **POST**

4. Agrega estos headers:
   ```
   Accept: application/vnd.github.v3+json
   Authorization: token TU_GITHUB_TOKEN
   Content-Type: application/json
   ```

5. En el body del request:
   ```json
   {"event_type": "run-update"}
   ```

6. Configura la frecuencia (1 vez al día)

### 3. Crear GitHub Personal Access Token

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Genera un nuevo token con el scope `repo`
3. Usa este token en el header `Authorization` de cronjob.org

## Ejecución Manual

También puedes ejecutar el workflow manualmente:

1. Ve a **Actions** en tu repositorio
2. Selecciona el workflow "Update Confluence to Google Sheets"
3. Click en **Run workflow**

## Estructura de Archivos

```
.
├── .github/
│   └── workflows/
│       └── update-confluence-sheets.yml
├── requirements.txt
├── UpdateFunctionalResults.py
├── UpdateDefectEficiencyRemoval.py
└── README.md
```

## Notas

- El workflow se ejecuta cuando cronjob.org envía el webhook
- También se puede ejecutar manualmente desde la pestaña Actions
- Los logs de ejecución están disponibles en GitHub Actions
