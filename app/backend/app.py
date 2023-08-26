import io
import logging
import mimetypes
import os
import time

import openai
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from flask import (
    Blueprint,
    Flask,
    abort,
    current_app,
    jsonify,
    request,
    send_file,
    send_from_directory,
)

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.readdecomposeask import ReadDecomposeAsk
from approaches.readretrieveread import ReadRetrieveReadApproach
from approaches.retrievethenread import RetrieveThenReadApproach

#
#
# Custom imports
#
#
from io import BytesIO
import base64
import re
import html
from pypdf import PdfReader, PdfWriter
import tempfile
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig
from azure.cognitiveservices.speech.audio import AudioConfig
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from tenacity import retry, stop_after_attempt, wait_random_exponential

MAX_SECTION_LENGTH = 1000
SENTENCE_SEARCH_LIMIT = 100
SECTION_OVERLAP = 100

#
#
# End of custom imports
#
#

# Replace these with your own values, either in environment variables or directly here
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "mystorageaccount")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "content")
AZURE_SEARCH_SERVICE = os.getenv("AZURE_SEARCH_SERVICE", "gptkb")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "gptkbindex")
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE", "myopenai")
AZURE_OPENAI_GPT_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_GPT_DEPLOYMENT", "davinci")
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chat")
AZURE_OPENAI_CHATGPT_MODEL = os.getenv(
    "AZURE_OPENAI_CHATGPT_MODEL", "gpt-35-turbo")
AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMB_DEPLOYMENT", "embedding")
AZURE_FORMRECOGNIZER_SERVICE = os.getenv("AZURE_FORMRECOGNIZER_SERVICE")

KB_FIELDS_CONTENT = os.getenv("KB_FIELDS_CONTENT", "content")
KB_FIELDS_CATEGORY = os.getenv("KB_FIELDS_CATEGORY", "category")
KB_FIELDS_SOURCEPAGE = os.getenv("KB_FIELDS_SOURCEPAGE", "sourcepage")

CONFIG_OPENAI_TOKEN = "openai_token"
CONFIG_CREDENTIAL = "azure_credential"
CONFIG_ASK_APPROACHES = "ask_approaches"
CONFIG_CHAT_APPROACHES = "chat_approaches"
CONFIG_BLOB_CLIENT = "blob_client"
CONFIG_SEARCH_CLIENT = "search_client"
CONFIG_DOCUMENT_ANALYSIS_CLIENT = "document_analysis_client"


bp = Blueprint("routes", __name__, static_folder='static')


@bp.route("/")
def index():
    return bp.send_static_file("index.html")


@bp.route("/favicon.ico")
def favicon():
    return bp.send_static_file("favicon.ico")


@bp.route("/assets/<path:path>")
def assets(path):
    return send_from_directory("static/assets", path)

# Serve content files from blob storage from within the app to keep the example self-contained.
# *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# can access all the files. This is also slow and memory hungry.


@bp.route("/content/<path>")
def content_file(path):
    blob_container = current_app.config[CONFIG_BLOB_CLIENT].get_container_client(
        AZURE_STORAGE_CONTAINER)
    blob = blob_container.get_blob_client(path).download_blob()
    if not blob.properties or not blob.properties.has_key("content_settings"):
        abort(404)
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob_file = io.BytesIO()
    blob.readinto(blob_file)
    blob_file.seek(0)
    return send_file(blob_file, mimetype=mime_type, as_attachment=False, download_name=path)


@bp.route("/ask", methods=["POST"])
def ask():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    approach = request.json["approach"]
    try:
        impl = current_app.config[CONFIG_ASK_APPROACHES].get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        r = impl.run(request.json["question"],
                     request.json.get("overrides") or {})
        return jsonify(r)
    except Exception as e:
        logging.exception("Exception in /ask")
        return jsonify({"error": str(e)}), 500


@bp.route("/chat", methods=["POST"])
def chat():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    approach = request.json["approach"]
    try:
        impl = current_app.config[CONFIG_CHAT_APPROACHES].get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        r = impl.run(request.json["history"],
                     request.json.get("overrides") or {})
        return jsonify(r)
    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500

#
#
# My code starts
#
#


# @bp.route("/get_search", methods=["POST"])
# def get_search():
#     try:
#         documents = []
#         search_client = current_app.config[CONFIG_SEARCH_CLIENT]
#         results = search_client.search(search_text="")

#         for result in results:
#             documents.append(result)

#         return jsonify(documents)
#     except Exception as e:
#         logging.exception("Exception in /get_search")
#         return jsonify({"error": str(e)}), 500


@bp.route("/get_documents", methods=["POST"])
def get_document_names():
    try:
        print("inside getDocuments")
        blob_data = dict()
        blob_container = current_app.config[CONFIG_BLOB_CLIENT].get_container_client(
            AZURE_STORAGE_CONTAINER)
        for blob in blob_container.list_blobs():
            full_blob_name = blob.name
            last_hyphen_index = full_blob_name.rfind("-")
            base_name = full_blob_name[:last_hyphen_index].strip()

            # If the name is already in the dictionary, only overwrite if the new date is earlier.
            if base_name in blob_data and blob_data[base_name][0] < blob.last_modified:
                continue

            blob_data[base_name] = (
                blob.last_modified, blob.etag)  # Convert to tuple

        return list(blob_data.items())  # Convert to list of tuples
    except Exception as e:
        logging.exception("Exception in /get_documents")
        return jsonify({"error": str(e)}), 500


@bp.route("/delete_document", methods=["POST"])
def delete_document():
    data = request.get_json()
    blob_name_to_delete = data.get('name')
    blob_client = current_app.config[CONFIG_BLOB_CLIENT]
    blob_container = current_app.config[CONFIG_BLOB_CLIENT].get_container_client(
        AZURE_STORAGE_CONTAINER)
    search_client = current_app.config[CONFIG_SEARCH_CLIENT]

    if not blob_name_to_delete:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    blob_list = blob_container.list_blobs()
    for blob in blob_list:
        if blob.name.startswith(blob_name_to_delete):
            try:
                # Delete blob from storage
                blob_client_del = blob_client.get_blob_client(
                    "content", blob.name)
                blob_client_del.delete_blob()
                print(f"Blob {blob.name} has been deleted.")

            except Exception as e:
                print(f"Failed to delete blob: {blob.name}. Error: {e}")

    # Create filter for search
    print(blob_name_to_delete)
    filter = f"sourcefile eq '{blob_name_to_delete}.pdf'"

    while True:
        print("got inside the while loop")
        # Search for documents to delete
        r = search_client.search(
            search_text="*", filter=filter, top=1000, include_total_count=True)
        results = list(r)
        print(f"Count of results: {len(results)}")
        for result in results:
            print(f"Results: {result}")
        if len(results) == 0:
            break
        r = search_client.delete_documents(
            documents=[{"id": d["id"]} for d in results])
        print(f"\tRemoved {len(r)} sections from index")
        # It can take a few seconds for search results to reflect changes, so wait a bit
        time.sleep(2)

    return "200"

#
#
# Uploading Documents
#
#


def index_sections(file, sections):
    print(
        f"Indexing sections from '{file.filename}' into search index")
    search_client = current_app.config[CONFIG_SEARCH_CLIENT]
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = search_client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            print(
                f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = search_client.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")


def before_retry_sleep(retry_state):
    print("Rate limited on the OpenAI embeddings API, sleeping before retrying...")


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(15), before_sleep=before_retry_sleep)
def compute_embedding(text):
    return openai.Embedding.create(engine="embedding", input=text)["data"][0]["embedding"]


def split_text(page_map):
    SENTENCE_ENDINGS = [".", "!", "?"]
    WORDS_BREAKS = [",", ";", ":", " ",
                    "(", ")", "[", "]", "{", "}", "\t", "\n"]

    def find_page(offset):
        num_pages = len(page_map)
        for i in range(num_pages - 1):
            if offset >= page_map[i][1] and offset < page_map[i + 1][1]:
                return i
        return num_pages - 1

    all_text = "".join(p[2] for p in page_map)
    length = len(all_text)
    start = 0
    end = length
    while start + SECTION_OVERLAP < length:
        last_word = -1
        end = start + MAX_SECTION_LENGTH

        if end > length:
            end = length
        else:
            # Try to find the end of the sentence
            while end < length and (end - start - MAX_SECTION_LENGTH) < SENTENCE_SEARCH_LIMIT and all_text[end] not in SENTENCE_ENDINGS:
                if all_text[end] in WORDS_BREAKS:
                    last_word = end
                end += 1
            if end < length and all_text[end] not in SENTENCE_ENDINGS and last_word > 0:
                end = last_word  # Fall back to at least keeping a whole word
        if end < length:
            end += 1

        # Try to find the start of the sentence or at least a whole word boundary
        last_word = -1
        while start > 0 and start > end - MAX_SECTION_LENGTH - 2 * SENTENCE_SEARCH_LIMIT and all_text[start] not in SENTENCE_ENDINGS:
            if all_text[start] in WORDS_BREAKS:
                last_word = start
            start -= 1
        if all_text[start] not in SENTENCE_ENDINGS and last_word > 0:
            start = last_word
        if start > 0:
            start += 1

        section_text = all_text[start:end]
        yield (section_text, find_page(start))

        last_table_start = section_text.rfind("<table")
        if (last_table_start > 2 * SENTENCE_SEARCH_LIMIT and last_table_start > section_text.rfind("</table")):
            # If the section ends with an unclosed table, we need to start the next section with the table.
            # If table starts inside SENTENCE_SEARCH_LIMIT, we ignore it, as that will cause an infinite loop for tables longer than MAX_SECTION_LENGTH
            # If last table starts inside SECTION_OVERLAP, keep overlapping
            start = min(end - SECTION_OVERLAP, start + last_table_start)
        else:
            start = end - SECTION_OVERLAP

    if start + SECTION_OVERLAP < end:
        yield (all_text[start:end], find_page(start))


def filename_to_id(filename):
    filename_ascii = re.sub("[^0-9a-zA-Z_-]", "_", filename)
    filename_hash = base64.b16encode(filename.encode('utf-8')).decode('ascii')
    return f"file-{filename_ascii}-{filename_hash}"


def create_sections(file, page_map, use_vectors):
    file_id = filename_to_id(file.filename)
    for i, (content, pagenum) in enumerate(split_text(page_map)):
        section = {
            "id": f"{file_id}-page-{i}",
            "content": content,
            "category": "category",
            "sourcepage": blob_name_from_file_page(file.filename, pagenum),
            "sourcefile": file.filename
        }
        if use_vectors:
            section["embedding"] = compute_embedding(content)
        yield section


def table_to_html(table):
    table_html = "<table>"
    rows = [sorted([cell for cell in table.cells if cell.row_index == i],
                   key=lambda cell: cell.column_index) for i in range(table.row_count)]
    for row_cells in rows:
        table_html += "<tr>"
        for cell in row_cells:
            tag = "th" if (
                cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
            cell_spans = ""
            if cell.column_span > 1:
                cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span > 1:
                cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html += "</tr>"
    table_html += "</table>"
    return table_html


def blob_name_from_file_page(filename, page=0):
    if os.path.splitext(filename)[1].lower() == ".pdf":
        return os.path.splitext(os.path.basename(filename))[0] + f"-{page}" + ".pdf"
    else:
        return os.path.basename(filename)


def upload_blobs(file):
    blob_container = current_app.config[CONFIG_BLOB_CLIENT].get_container_client(
        AZURE_STORAGE_CONTAINER)
    if not blob_container.exists():
        blob_container.create_container()

    # if file is PDF split into pages and upload each page as a separate blob
    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(file)
        pages = reader.pages
        for i in range(len(pages)):
            blob_name = blob_name_from_file_page(file.filename, i)
            f = io.BytesIO()
            writer = PdfWriter()
            writer.add_page(pages[i])
            writer.write(f)
            f.seek(0)
            blob_container.upload_blob(blob_name, f, overwrite=True)
    else:
        blob_name = blob_name_from_file_page(file.filename)
        # with open(file, "rb") as data:
        file.seek(0)
        blob_container.upload_blob(blob_name, file, overwrite=True)


def get_document_text(file):
    offset = 0
    page_map = []

    file.seek(0)
    # Create a temporary file
    temp = tempfile.NamedTemporaryFile(delete=False)

    # Write the contents of the uploaded file to this temporary file
    file_content = file.read()
    temp.write(file_content)
    temp.close()

    # Ensure we're not dealing with an empty file
    if not file_content:
        raise ValueError("The uploaded file is empty.")

    reader = PdfReader(temp.name)
    pages = reader.pages
    for page_num, p in enumerate(pages):
        page_text = p.extract_text()
        page_map.append((page_num, offset, page_text))
        offset += len(page_text)
    print(
        f"Extracting text from '{file.filename}' using Azure Form Recognizer")
    form_recognizer_client = current_app.config[CONFIG_DOCUMENT_ANALYSIS_CLIENT]
    with open(temp.name, "rb") as f:
        poller = form_recognizer_client.begin_analyze_document(
            "prebuilt-layout", document=f)
    form_recognizer_results = poller.result()

    for page_num, page in enumerate(form_recognizer_results.pages):
        tables_on_page = [
            table for table in form_recognizer_results.tables if table.bounding_regions[0].page_number == page_num + 1]

        # mark all positions of the table spans in the page
        page_offset = page.spans[0].offset
        page_length = page.spans[0].length
        table_chars = [-1]*page_length
        for table_id, table in enumerate(tables_on_page):
            for span in table.spans:
                # replace all table spans with "table_id" in table_chars array
                for i in range(span.length):
                    idx = span.offset - page_offset + i
                    if idx >= 0 and idx < page_length:
                        table_chars[idx] = table_id

        # build page text by replacing charcters in table spans with table html
        page_text = ""
        added_tables = set()
        for idx, table_id in enumerate(table_chars):
            if table_id == -1:
                page_text += form_recognizer_results.content[page_offset + idx]
            elif table_id not in added_tables:
                page_text += table_to_html(tables_on_page[table_id])
                added_tables.add(table_id)

        page_text += " "
        page_map.append((page_num, offset, page_text))
        offset += len(page_text)

    return page_map


def transcribe_audio(file_name):
    print("inside the transcribe function")

    # Setup SpeechConfig
    speech_config = SpeechConfig(
        subscription="4cee7ff91f544cd8973977a2668bf540", region="eastus")
    speech_config.speech_recognition_language = "en-US"

    # Setup AudioConfig
    audio_config = AudioConfig(filename=file_name)

    # Create a speech recognizer
    speech_recognizer = SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config)

    # Define a dict for storing status
    done_dict = {'done': False}

    # Define a list for storing recognized text
    recognized_text = []

    def stop_cb(evt):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        speech_recognizer.stop_continuous_recognition()
        done_dict['done'] = True

    def recognized_cb(evt):
        """callback that appends recognized text to recognized_text list"""
        print('RECOGNIZED: {}'.format(evt))
        recognized_text.append(evt.result.text + '\n')

    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # This will start the recognition process.
    speech_recognizer.start_continuous_recognition()

    while not done_dict['done']:
        time.sleep(.5)

    # Join the recognized text into one string
    full_text = ' '.join(recognized_text)
    print("\nFull text: ", full_text)
    return full_text


def generate_pdf(transcript, output_path):
    print("given transcript")
    print(transcript)
    print(output_path)
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 10)

    # Start at the top of the page (minus some margin)
    y_position = height - 40
    try:
        for line in transcript.split('\n'):
            if y_position <= 40:  # If close to the bottom of the page, create a new page
                c.showPage()
                y_position = height - 40  # Reset the y position for the new page
            textobject = c.beginText(40, y_position)
            textobject.textLine(line)
            c.drawText(textobject)
            y_position -= 14  # Move down by the line height
        c.showPage()
    finally:
        c.save()
    return output_path


# This is an in-memory example; in a real application, you might use a database
file_statuses = {}


@bp.route("/upload_document", methods=["POST"])
def upload_document():
    if 'file' not in request.files:
        return 'No file part in the request', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400

    # detect whether the file is an audio file
    mimetype = mimetypes.guess_type(file.filename)[0]
    if mimetype and mimetype.startswith('audio'):
        print(f"Processing audio file")
        # Save the audio file temporarily
        audio_path = os.path.join(
            tempfile.gettempdir(), file.filename)
        file.save(audio_path)

        # Transcribe the audio to text
        file_statuses[file.filename] = 'Transcribing Audio File'
        transcript = transcribe_audio(audio_path)
        os.remove(audio_path)

        file_statuses[file.filename] = 'Generating PDF'
        # Save transcript to PDF
        pdf_tmp_filepath = os.path.join(
            tempfile.gettempdir(), f'{os.path.splitext(file.filename)[0]}.pdf')
        generate_pdf(transcript, pdf_tmp_filepath)

        # Read PDF into BytesIO object
        with open(pdf_tmp_filepath, 'rb') as f:
            pdf_bytes = f.read()
        pdf_file = BytesIO(pdf_bytes)
        pdf_file.filename = f'{os.path.splitext(file.filename)[0]}.pdf'

        # Remove temporary PDF file
        os.remove(pdf_tmp_filepath)
        print(f"Generated PDF")
        # Upload the generated PDF
        file_statuses[file.filename] = 'Uploading'
        upload_blobs(pdf_file)
        page_map = get_document_text(pdf_file)
        sections = create_sections(pdf_file, page_map)
        index_sections(pdf_file, sections)
        file_statuses[file.filename] = 'Uploaded'
    else:
        print(f"Uploading file")
        tmp_filepath = os.path.join(
            tempfile.gettempdir(), file.filename)
        file.save(tmp_filepath)
        file_statuses[file.filename] = 'Uploading'
        upload_blobs(file)
        page_map = get_document_text(file)
        file_statuses[file.filename] = 'Processing'
        sections = create_sections(file, page_map, True)
        index_sections(file, sections)
        file_statuses[file.filename] = 'Uploaded'
        # for get_document_text, create_sections, and index_sections, you might need to adjust those functions
        # or save the file temporarily if they also need to read the file content

    return 'File successfully uploaded', 200


@bp.route('/file_status/<file_name>', methods=['GET'])
def file_status(file_name):
    return jsonify(status=file_statuses.get(file_name, 'Pending'))


#
#
# My code ends
#
#


@bp.before_request
def ensure_openai_token():
    openai_token = current_app.config[CONFIG_OPENAI_TOKEN]
    if openai_token.expires_on < time.time() + 60:
        openai_token = current_app.config[CONFIG_CREDENTIAL].get_token(
            "https://cognitiveservices.azure.com/.default")
        current_app.config[CONFIG_OPENAI_TOKEN] = openai_token
        openai.api_key = openai_token.token


# Rest of app
def create_app():
    app = Flask(__name__)

    # Use the current user identity to authenticate with Azure OpenAI, Cognitive Search and Blob Storage (no secrets needed,
    # just use 'az login' locally, and managed identity when deployed on Azure). If you need to use keys, use separate AzureKeyCredential instances with the
    # keys for each service
    # If you encounter a blocking error during a DefaultAzureCredntial resolution, you can exclude the problematic credential by using a parameter (ex. exclude_shared_token_cache_credential=True)
    azure_credential = DefaultAzureCredential(
        exclude_shared_token_cache_credential=True)

    # Set up clients for Cognitive Search and Storage
    search_client = SearchClient(
        endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
        index_name=AZURE_SEARCH_INDEX,
        credential=azure_credential)
    blob_client = BlobServiceClient(
        account_url=f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=azure_credential)
    document_analysis_client = DocumentAnalysisClient(
        endpoint=f"https://{AZURE_FORMRECOGNIZER_SERVICE}.cognitiveservices.azure.com/", credential=azure_credential, headers={"x-ms-useragent": "azure-search-chat-demo/1.0.0"})

    # Used by the OpenAI SDK
    openai.api_type = "azure"
    openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
    openai.api_version = "2023-05-15"

    # Comment these two lines out if using keys, set your API key in the OPENAI_API_KEY environment variable instead
    openai.api_type = "azure_ad"
    openai_token = azure_credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    )
    openai.api_key = openai_token.token

    # Store on app.config for later use inside requests
    app.config[CONFIG_OPENAI_TOKEN] = openai_token
    app.config[CONFIG_CREDENTIAL] = azure_credential
    app.config[CONFIG_BLOB_CLIENT] = blob_client
    app.config[CONFIG_SEARCH_CLIENT] = search_client
    app.config[CONFIG_DOCUMENT_ANALYSIS_CLIENT] = document_analysis_client
    # Various approaches to integrate GPT and external knowledge, most applications will use a single one of these patterns
    # or some derivative, here we include several for exploration purposes
    app.config[CONFIG_ASK_APPROACHES] = {
        "rtr": RetrieveThenReadApproach(
            search_client,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT
        ),
        "rrr": ReadRetrieveReadApproach(
            search_client,
            AZURE_OPENAI_GPT_DEPLOYMENT,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT
        ),
        "rda": ReadDecomposeAsk(search_client,
                                AZURE_OPENAI_GPT_DEPLOYMENT,
                                AZURE_OPENAI_EMB_DEPLOYMENT,
                                KB_FIELDS_SOURCEPAGE,
                                KB_FIELDS_CONTENT
                                )
    }
    app.config[CONFIG_CHAT_APPROACHES] = {
        "rrr": ChatReadRetrieveReadApproach(
            search_client,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        )
    }

    app.register_blueprint(bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
