import os
from fastapi import HTTPException, UploadFile
import pandas as pd
from backend.core.state import StudioPhase, StudioState

ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.html'}
MAX_FILE_SIZE_MB = 100


class DataIngestionAgent:
    def ingest(self, file: UploadFile) -> StudioState:
        state = StudioState(current_phase=StudioPhase.DATA_UPLOADED)
        try:
            filename = file.filename
            if not filename:
                raise HTTPException(status_code=400, detail="Invalid file name")
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                state.errors.append(f"Unsupported file extension: {ext}")
                raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

            contents = file.file.read()
            file_size_mb = len(contents) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                state.errors.append("File size exceeds 100MB limit.")
                raise HTTPException(status_code=400, detail="File size exceeds 100MB limit.")

            # Load DataFrame
            if ext == '.csv':
                df = pd.read_csv(pd.io.common.BytesIO(contents))
            elif ext == '.xlsx':
                df = pd.read_excel(pd.io.common.BytesIO(contents))
            elif ext == '.html':
                dfs = pd.read_html(pd.io.common.BytesIO(contents))
                df = dfs[0] if dfs else None
                if df is None:
                    state.errors.append("No table found in HTML file.")
                    raise HTTPException(status_code=400, detail="No table found in HTML file.")
            else:
                state.errors.append("Unknown error.")
                raise HTTPException(status_code=400, detail="Unknown error.")

            # Normalize columns
            df.columns = [str(col).strip().lower() for col in df.columns]

            state.raw_file_name = filename
            state.dataframe_shape = df.shape
            state.dataframe_columns = list(df.columns)
            state.file_size_mb = round(file_size_mb, 2)
            state.dataframe = df
            state.current_phase = StudioPhase.DATA_UPLOADED
            return state
        except HTTPException as e:
            raise e
        except Exception as e:
            state.errors.append(str(e))
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
