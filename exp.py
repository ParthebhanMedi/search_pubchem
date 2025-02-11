import streamlit as st
import requests
from json import loads
from PIL import Image
from io import BytesIO

# Streamlit title
st.title("PubChem Search Interface")
st.sidebar.title("Search Methods")


# Define the Base URL for the PubChem PUG REST API
BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


# Initialize session state for storing CIDs list for Similarity Search
if "similarity_cids" not in st.session_state:
    st.session_state["similarity_cids"] = []

# Helper function to fetch data
def fetch_data(endpoint, params=None, method="GET"):
    """Helper function to fetch data from PubChem API."""
    try:
        if method == "GET":
            response = requests.get(endpoint, params=params)
        elif method == "POST":
            response = requests.post(endpoint, data=params)

        # Check for a successful request
        if response.status_code == 200:
            return response
        else:
            st.error(f"Error {response.status_code}: {response.reason}")
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
    return None

# Function to display the structure of a compound by CID
def display_structure(cid):
    """Display the image of a compound given its CID."""
    image_url = f"{BASE_URL}/compound/cid/{cid}/record/PNG?image_size=600x600"
    response = requests.get(image_url)
    if response.status_code == 200:
        # Load the image via Pillow
        img = Image.open(BytesIO(response.content))
        # Resize the image to desired dimensions (e.g., 300x300)
        img = img.resize((600, 600))  # Adjust as needed
        # Display the resized image
        st.image(
            img,
            caption=f"CID {cid}",
        )
    else:
        st.error(f"Could not retrieve image for CID {cid}")

# ---- Helper for "View All Compounds" Logic ----
def handle_view_all():
    """Display all compounds for the stored CIDs in session state."""
    if not st.session_state["similarity_cids"]:
        st.warning("No compounds to display. Perform a search first.")
    else:
        for cid in st.session_state["similarity_cids"]:
            display_structure(cid)


# Sidebar options for search methods
st.sidebar.subheader("Search Options")
search_method = st.sidebar.radio(
    "Choose a search method:",
    (
        "By CID",       
        "By Name",
        "By SMILES",
        "By Molecular Formula",
        "By Mass",
        "By Structure Search (Substructure/Superstructure)",
        "View Full Records",
        "By Similarity Search",
    ),
)

st.sidebar.write(" ")
st.sidebar.write(" ")
st.sidebar.write("Created by: Parthebhan Pari")
st.sidebar.write("Last updated : 11-02-2025")

# ---- Search compound by CID ----
if search_method == "By CID":
    st.subheader("Search by CID")
    cid = st.text_input("Enter PubChem CID:", "2244")
    if st.button("Search"):
        # Fetch compound data and structure
        data = fetch_data(f"{BASE_URL}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,SMILES/JSON")
        if data:
            st.json(loads(data.text))
            display_structure(cid)

# ---- Similarity Search ----
elif search_method == "By Similarity Search":
    st.subheader("Search by Similarity")
    smiles = st.text_input("Enter SMILES string for similarity search:", "CC(=O)OC1=CC=CC=C1C(=O)O")
    threshold = st.slider("Similarity Threshold (1-100):", min_value=1, max_value=100, value=90)

    if st.button("Search"):
        # Fetch similar compounds
        endpoint = f"{BASE_URL}/compound/fastsimilarity_2d/smiles/cids/TXT?Threshold={threshold}"
        response = fetch_data(endpoint, {"smiles": smiles}, method="POST")
        if response and response.text.strip():
            st.session_state["similarity_cids"] = response.text.strip().split()  # Store CIDs in session state
            st.write(f"Found {len(st.session_state['similarity_cids'])} similar compounds.")
            st.write(f"CIDs: {st.session_state['similarity_cids']}")
        else:
            st.error("No similar compounds found.")

    # Add a "View All" button
    if st.button("View All Compounds"):
        handle_view_all()

# ---- Combined SDF and JSON (New Block) ----
elif search_method == "View Full Records":
    st.subheader("View or Download Full Record")
    cid = st.text_input("Enter PubChem CID for SDF and JSON:", "2244")  # Input for CID
    
    # JSON View Block
    if st.button("View as JSON"):
        json_url = f"{BASE_URL}/compound/cid/{cid}/JSON"  # URL to fetch JSON response
        response = fetch_data(json_url)
        if response:
            st.success(f"Successfully retrieved the JSON response for CID {cid}.")
            st.write("### JSON Response:")
            st.json(response.json())  # Display JSON data
        else:
            st.error("Failed to retrieve the JSON response. Please ensure the CID is correct.")

    # SDF Download Block
    if st.button("Download SDF"):
        sdf_url = f"{BASE_URL}/compound/cid/{cid}/SDF"  # URL to fetch SDF file
        response = fetch_data(sdf_url)
        if response:
            st.success(f"Successfully retrieved the SDF file for CID {cid}.")
            # Create a download button for the SDF file
            st.download_button(
                label="Download SDF File",
                data=response.content,  # File content
                file_name=f"CID_{cid}.sdf",  # Suggested filename
                mime="chemical/x-mdl-sdfile"  # MIME type for SDF files
            )
        else:
            st.error("Failed to retrieve the SDF file. Please ensure the CID is correct.")


# ---- Search compound by Name ----
elif search_method == "By Name":
    st.subheader("Search by Name")
    name = st.text_input("Enter chemical name (e.g., glucose):", "glucose")
    if st.button("Search"):
        # Fetch CIDs by name
        cids = fetch_data(f"{BASE_URL}/compound/name/{name}/cids/TXT")
        if cids and cids.text.strip():
            cids_list = cids.text.strip().split()
            st.write(f"Found CIDs: {cids_list}")
            # Display properties and structures for each CID
            for cid in cids_list:
                st.write(f"**CID {cid}**:")
                display_structure(cid)
            
            
# ---- By SMILES Search ----
elif search_method == "By SMILES":
    st.subheader("Search by SMILES")
    smiles = st.text_input("Enter SMILES string:", "CC(=O)OC1=CC=CC=C1C(=O)O")
    if st.button("Search"):
        # Fetch CID by SMILES
        cids = fetch_data(f"{BASE_URL}/compound/smiles/{smiles}/cids/TXT")
        if cids:
            cids_list = cids.text.strip().split()
            st.write(f"Found CIDs: {cids_list}")
            for cid in cids_list:
                display_structure(cid)

# ---- By Molecular Formula Search ----
elif search_method == "By Molecular Formula":
    st.subheader("Search by Molecular Formula")
    formula = st.text_input("Enter molecular formula (e.g., H2O):", "C6H12O6")
    if st.button("Search"):
        # Fetch CIDs by molecular formula
        cids = fetch_data(f"{BASE_URL}/compound/fastformula/{formula}/cids/TXT")
        if cids:
            cids_list = cids.text.strip().split()
            st.write(f"Found CIDs: {cids_list}")
            for cid in cids_list:
                display_structure(cid)

# ---- By Mass Search ----
elif search_method == "By Mass":
    st.subheader("Search by Mass")
    mass_type = st.selectbox("Mass Type:", ["molecular_weight", "exact_mass", "monoisotopic_mass"])
    mass_input_type = st.radio("Search Method:", ["Equals a Value", "Within Range"])
    if mass_input_type == "Equals a Value":
        mass_value = st.number_input(f"Enter {mass_type}:", step=0.001, value=400.0)
        if st.button("Search Mass"):
            endpoint = f"{BASE_URL}/compound/{mass_type}/equals/{mass_value}/cids/TXT"
            cids = fetch_data(endpoint)
            if cids:
                cids_list = cids.text.strip().split()
                st.write(f"Found CIDs: {cids_list}")
                for cid in cids_list:
                    display_structure(cid)
    elif mass_input_type == "Within Range":
        mass_min = st.number_input(f"Enter Minimum {mass_type}:", step=0.001, value=400.0)
        mass_max = st.number_input(f"Enter Maximum {mass_type}:", step=0.001, value=400.05)
        if st.button("Search Mass"):
            endpoint = f"{BASE_URL}/compound/{mass_type}/range/{mass_min}/{mass_max}/cids/TXT"
            cids = fetch_data(endpoint)
            if cids:
                cids_list = cids.text.strip().split()
                st.write(f"Found CIDs: {cids_list}")
                for cid in cids_list:
                    display_structure(cid)

# ---- By Structure Search (Substructure/Superstructure) ----
elif search_method == "By Structure Search (Substructure/Superstructure)":
    st.subheader("Search by Structure")
    smiles = st.text_input("Enter substructure or superstructure SMILES string:", "C1CCCCC1")
    search_type = st.selectbox("Search Type:", ["substructure", "superstructure"])  # Select between substructure/superstructure

    if st.button("Search"):
        # Use the correct search type based on the user's input
        endpoint = f"{BASE_URL}/compound/fast{search_type}/smiles/cids/TXT"
        cids = fetch_data(endpoint, {"smiles": smiles}, method="POST")
        if cids:
            cids_list = cids.text.strip().split()
            st.write(f"Found CIDs: {cids_list}")
            for cid in cids_list:
                display_structure(cid)

# ---- By Cross Reference ----
elif search_method == "By Cross Reference":
    st.subheader("Search by Cross Reference")
    xref_type = st.text_input("Enter cross-reference type (e.g., PatentID):", "PatentID")
    xref_value = st.text_input("Enter cross-reference value:", "US20050159403A1")
    if st.button("Search"):
        endpoint = f"{BASE_URL}/substance/xref/{xref_type}/{xref_value}/sids/JSON"
        sids = fetch_data(endpoint)
        if sids:
            st.json(loads(sids))
