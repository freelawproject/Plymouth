Plymouth

    Plymouth is a Python library for collecting data from 

Installation

    Install requirements.txt

Usage

    VALID_ACTIONS = {
        "get-pacer-ids": get_pacer_ids,
        "get-dockets": download_json_html,
        "get-pdfs": get_pdfs,
        "zip-files": zip_files,
    }
    
    python main.py --action ANY VALID ACTION ABOVE
    Preferably in the order listed. 

License

    MIT