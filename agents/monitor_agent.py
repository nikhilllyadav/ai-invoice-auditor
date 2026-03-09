import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import logging
from concurrent.futures import ProcessPoolExecutor # 1. Import Executor
from logs.logger_module import setup_logger
from agents.agent_graph import app
import threading

# Setup the logger
logger = setup_logger(__name__, log_file="logs/my_app.log", level=logging.DEBUG)

folder_path = 'data/incoming/'
supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.txt']

# 2. Define the processing function at the top level (required for multiprocessing)
def run_graph_task(file_path):
    """This function runs in a separate subprocess."""
    file_name = os.path.basename(file_path)
    try:
        logger.info(f"Starting Parallel Process for: {file_name}")
        # Ensure the graph and config are handled inside the worker
        config = {"configurable": {"thread_id": file_name.lower()}}
        app.invoke({"document_name": Path(file_path)}, config=config)
        logger.info(f"Successfully processed: {file_name}")
    except Exception as e:
        logger.error(f"Error processing {file_name}: {str(e)}")

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, executor, debounce_seconds=2.0):
        self.executor = executor
        self.debounce_seconds = debounce_seconds
        self.timers = {}  # Tracks timers for each batch/thread_id

    def on_created(self, event):
        if event.is_directory:
            return

        # 1. Extract the base name (e.g., 'Invoice_01' from 'Invoice_01.pdf')
        # This acts as our unique key to group the PDF and JSON together.
        file_path = Path(event.src_path)
        batch_id = file_path.stem.replace("_meta", "") 

        if any(file_path.suffix.lower() in ext for ext in supported_extensions):
            # 2. If a timer is already running for this file ID, cancel it
            if batch_id in self.timers:
                self.timers[batch_id].cancel()

            # 3. Start (or restart) a timer. 
            # Only when the folder "goes quiet" for X seconds will the graph trigger.
            t = threading.Timer(
                self.debounce_seconds, 
                self.executor.submit, 
                args=[run_graph_task, str(file_path)]
            )
            self.timers[batch_id] = t
            t.start()
            logger.info(f"Queuing {batch_id}... waiting for related files.")

def watch_folder():
    # 4. Initialize the Executor. 'max_workers' defines how many parallel graphs can run.
    # If not specified, it defaults to the number of processors on your machine.
    with ProcessPoolExecutor(max_workers=4) as executor:
        event_handler = FileEventHandler(executor)
        observer = Observer()
        observer.schedule(event_handler, folder_path, recursive=False)
        observer.start()
        
        logger.info(f"Monitoring started on {folder_path}...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("Stopping monitor...")
        observer.join()

if __name__ == "__main__":
    watch_folder()