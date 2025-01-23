import os, time, random, re, threading, time
import streamlit as st # type: ignore
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from backend import ConnectionManager, websocket_endpoint,get_connected_users
from gpt4all import GPT4All # type: ignore
from st_draggable_list import DraggableList # type: ignore
import numpy as np # type: ignore
import pandas as pd # type: ignore
import scipy.stats as stats # type: ignore
from fuzzywuzzy import process # type: ignore
import matplotlib.pyplot as plt # type: ignore
from database import get_engine_alone,get_engine, get_session, insert_user_results_to_db,insert_user_info_to_db, UserResults, UserInfo,insert_user_questions_to_db,insert_user_results_alone;
from lobby_functions import get_modalita,send_previous_list_to_backend,send_message,chatroom,fetch_messages,fetch_connected_users,check_chat_partner,send_list_to_backend,next_page,prev_page,get_shared_list,generate_unique_key, send_continua_message
from groq import Groq
from apikey import GROQ_API_KEY

items = [
    {"id": 1, "name": "Scatola di Fiammiferi"},
    {"id": 2, "name": "Concentrato Alimentare"},
    {"id": 3, "name": "Corda in nylon di 15 metri"},
    {"id": 4, "name": "Paracadute di seta"},
    {"id": 5, "name": "Unità di Riscaldamento Portatile"},
    {"id": 6, "name": "Due pistole calibro .45"},
    {"id": 7, "name": "Latte disidratato"},
    {"id": 8, "name": "Bombole di ossigeno di 45kg"},
    {"id": 9, "name": "Mappa delle stelle"},
    {"id": 10, "name": "Zattera di salvataggio autogonfiabile"},
    {"id": 11, "name": "Bussola Magnetica"},
    {"id": 12, "name": "20 litri d'acqua"},
    {"id": 13, "name": "Razzo di segnalazione"},
    {"id": 14, "name": "Cassa di pronto soccorso"},
    {"id": 15, "name": "Radiolina alimentata con energia solare"}
]

# variabili di stato
if 'alone' not in st.session_state:
    st.session_state.alone = False
if 'modalita' not in st.session_state:
    st.session_state.modalita = ""
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'response_mode' not in st.session_state:
    st.session_state.response_mode = ""
if "last_user_input" not in st.session_state:
        st.session_state.last_user_input = ""
if "user_list" not in st.session_state:
        st.session_state.user_list = []
if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ""
          
if 'previous_list_text' not in st.session_state:
    st.session_state.previous_list_text = ""
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'llm_response_generated' not in st.session_state:
    st.session_state.llm_response_generated = False
if 'llm_response' not in st.session_state:
    st.session_state.llm_response = ""
if 'updated_list' not in st.session_state:
    st.session_state.updated_list = []  
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'previous_list' not in st.session_state:
    st.session_state.previous_list = items
if 'partner' not in st.session_state:
    st.session_state.partner = ""
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'valid' not in st.session_state:
    st.session_state.valid = "not valid"
    
if 'continua' not in st.session_state:
    st.session_state.continua = False
    
#chat con il LLM per la modalità individuale
def chat_with_model():
    st.sidebar.title("Chatta con il LLM")

    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    user_input = st.sidebar.text_input("Inserisci un messaggio:")

    response_mode = st.sidebar.radio(
        "Tipo di risposta",
        options=["Breve", "Dettagliata"]
    )
    # Only update response mode in session state if it has changed
    if response_mode != st.session_state.response_mode:
        st.session_state.response_mode = response_mode

    if (st.sidebar.button("Invia") or user_input) and user_input != st.session_state.last_user_input:
        
        st.session_state.conversation.append({"role": "user", "content": user_input})
        st.session_state.last_user_input = user_input

        client = Groq(api_key=GROQ_API_KEY)  

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
        {
            "role": "system",
            "content": "Sei un assistente dell'utente"
        },
        {
            "role": "user",
            "content": user_input + ", rispondi in maniera" + response_mode + "e in italiano"
        }
    ],
            temperature=0.75,
            max_tokens=400,
            top_p=1,
            stream=True,
            stop=None,
        )

        ai_response = ""
        for chunk in completion:
            ai_response += chunk.choices[0].delta.content or ""

        
        st.session_state.conversation.append({"role": "assistant", "content": ai_response})

   
    for msg in st.session_state.conversation:
        if msg["role"] == "user":
            st.sidebar.write("**You:**", msg["content"])
        else:
            st.sidebar.write("**AI:**", msg["content"])
            


    
BASE_URL = "http://127.0.0.1:8000"

hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


st.markdown(
        """
        <style>
            /* Custom CSS for the wide page layout */
            .stApp > div[data-testid="stVerticalBlock"] {
                max-width: 90%;
                margin: auto;
                padding: 20px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

st.markdown("""
    <style>
    .big-button {
        font-size: 20px !important;  /* Change font size */
        padding: 15px 25px !important;  /* Change padding */
        background-color: #4CAF50 !important;  /* Custom background color */
        color: white !important;  /* Custom text color */
        border-radius: 10px !important;  /* Rounded edges */
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

def highlight_closeness(row):

    initial_diff = abs(row['La tua lista iniziale'] - row['Lista ufficiale NASA'])
    final_diff = abs(row['La tua lista finale'] - row['Lista ufficiale NASA'])
    styles = [''] * len(row)  
    #Dà una colorazione in base al migliroamento o al peggioramentoo
    if final_diff < initial_diff:
        styles[2] = 'background-color: lightgreen'  
    elif final_diff > initial_diff:
        styles[2] = 'background-color: lightcoral'

    return styles

def calculate_weight_of_advice(final_estimate, initial_estimate, advice):
    numerator = abs(final_estimate - initial_estimate)
    denominator = abs(advice - initial_estimate)
    
    if denominator == 0:
        return None
    
    weight_of_advice = numerator / denominator
    return weight_of_advice

def extract_ai_ranking(llm_response):
    #pattern del regex 
    pattern = r"\d+\.\s*\*\*(.*?)\*\*"
    matches = re.findall(pattern, llm_response)

    if matches:
        #dizionario con i ranking ai
        ai_ranking = {item.strip(): idx + 1 for idx, item in enumerate(matches)}
        return ai_ranking
    else:
        #pattern alternativo
        pattern = r"\d+\.\s*([^\n]+?)\s*[\n-]" 
        matches = re.findall(pattern, llm_response)
        ai_ranking2 = {item.strip(): idx + 1 for idx, item in enumerate(matches)}
        return ai_ranking2

def next_page():
    st.session_state.page += 1

    st.rerun()

def prev_page():

    if st.session_state.page > 1:
        st.session_state.page -= 1
        st.rerun()

#normalizzazione dei nomi generati dall'ai
def get_best_match(item, choices, threshold=80):

        best_match, score = process.extractOne(item, choices)
        if score >= threshold:
            return best_match
        return None
    
# Page 1: inizio ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if st.session_state.page == 1:
    
    #Titolo in CSS
    st.markdown("""
        <style>
        .big-title {
            font-size: 50px;
            font-weight: bold;
            color: #ffffff;
            text-align: left;
        }
        </style>
    """, unsafe_allow_html=True)

    
    st.markdown('<p class="big-title">Ranking Interattivo con LLM</p>', unsafe_allow_html=True)

    st.write("L'esperimento è composto da 4 passaggi e si basa sull'interazione con un Large Language Model (LLM), che è un modello di intelligenza artificiale basato su testo. Un esempio di LLM è ChatGPT.")
    st.write("---------")
    st.markdown ("I passaggi sono i seguenti:")

    st.write("### 1) Compilare un questionario")
    st.write("")

    st.write("### 2) Stilare una classifica individualmente")
    st.write("_Dovrai ordinare 15 oggetti in base alle istruzioni che ti verranno fornite._")
    st.write("")

    st.write("### 3) Modificare la classifica in base al suggerimento del LLM")
    st.write("_Questo passaggio può essere fatto individualmente o con un'altra persona._")
    st.write("")

    st.write("### 4) Visualizzare i risultati")
    st.write("_Le due classifiche verranno confrontate con la classifica esatta della NASA e verranno mostrati alcuni dati._")
    st.write("")

    st.write("------------")
    if st.button("Avanti"):
        next_page()
        
# Page 2 : Questionario-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
elif st.session_state.page == 2:
    
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    
    domande_iniziali = ["Età" , "Sesso" , "Professione" , "Esperienza con i LLM (ex. ChatGPT)" ]    
    
    st.title("Questionario iniziale")
    st.write("------------------")
    domande = [
    "Dico agli altri cosa fare se vogliono essere ricompensati per il loro lavoro.",
    "Offro riconoscimenti/ricompense quando gli altri raggiungono i loro obiettivi.",
    "Faccio sapere ciò che gli altri possono ottenere per quello che fanno.",
    "Aiuto gli altri a migliorarsi.",
    "Faccio sapere agli altri come penso che stiano andando.",
    "Do attenzione personale a coloro che sembrano essere rifiutati.",
    "Faccio sentire bene gli altri quando stanno intorno a me.",
    "Gli altri hanno completa fiducia in me.",
    "Gli altri sono orgogliosi di essere associati a me.",
    "Esprimo con poche semplici parole cosa potremmo e dovremmo fare.",
    "Fornisco immagini accattivanti su ciò che possiamo fare.",
    "Aiuto gli altri a trovare un significato nel loro lavoro.",
    "Permetto agli altri di riflettere sui vecchi problemi in modi nuovi.",
    "Fornisco agli altri nuove prospettive per cose complicate.",
    "Alle persone faccio ripensare idee che non avevano mai messo in discussione.",
    "Sono soddisfatto di lasciare che gli altri continuino a lavorare nella stessa maniera di sempre.",
    "Qualsiasi cosa vogliano fare gli altri va bene per me.",
    "Non chiedo agli altri più di quanto sia assolutamente essenziale.",
    "Sono soddisfatto quando gli altri raggiungono gli standard concordati.",
    "Finché le cose funzionano, cerco di non cambiare nulla.",
    "Dico agli altri gli standard che devono conoscere per svolgere il loro lavoro."
]
    risposte_personali = {}
    risposte_questionario = {}
    
    
    st.subheader("Informazioni personali")
    age = st.number_input("Età", min_value=1, max_value=120,value=st.session_state.get("age", 18), placeholder = 18)
    gender = st.selectbox("Sesso", ["Donna", "Uomo", "Preferisco non dirlo","Altro"])
    profession = st.text_input("Professione", placeholder="Inserisci la tua professione")
    llm_experience = st.radio("Quanto frequentemente utilizzi i Large Language Models (LLM)? (Esempio di LLM : ChatGPT)", ["Mai usati" , "Raramente" , "Qualche volta" , "Spesso" , "Molto Spesso"] , horizontal = False)
    st.write("--------------")
    risposte_personali["eta"] = age
    risposte_personali["sesso"] = gender
    risposte_personali["professione"] = profession
    risposte_personali["esperienzaLLM"] = llm_experience

    #form per le risposte
    with st.form("questionnaire_form"):
 
        st.subheader("Questionario sulla leadership")
        st.write("Di seguito sono riportate 21 affermazioni. Per ciascuna, indica con quale frequenza ti riconosci in essa. ")
        st.write("""
            **Legenda:**
            - **0** : Mai
            - **1** : Raramente
            - **2** : Qualche volta
            - **3** : Spesso
            - **4** : Molto spesso
            """)

        st.write("")
        
        for i, question in enumerate(domande):
            st.write(f"{i + 1}. {question}")
            score = st.radio("question" ,  [0,1, 2, 3, 4], index=0,horizontal = True, key=f"q{i + 1}", label_visibility = "collapsed")
            risposte_questionario[i+1] = score
            st.write("---")

        submitted = st.form_submit_button("Conferma e prosegui")

        if submitted:
            st.session_state.risposte_personali = risposte_personali
            st.session_state.risposte_questionario = risposte_questionario
            next_page()
    
   
    st.components.v1.html("""
            <script>
                window.parent.document.getElementById('top').scrollIntoView({behavior: 'instant'});
            </script>
            """, height=0)
       
# Page 2: Draggable List ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
elif st.session_state.page == 3:
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.title("Sopravvivenza sulla Luna")
    st.write("-----------------")
    st.subheader("Scenario iniziale:")
    st.write("Sei il membro di un equipaggio spaziale destinato ad atterrare sulla luna. L'obiettivo è atterrare vicino all'astronave madre che al momento si trova sulla superficie lunare. Tuttavia, a causa di difficoltà meccaniche, la tua navicella è stata costretta ad atterrare a 200 chilometri dall'astronave madre. Durante l'atterraggio, l'astronave non è funzionante e gli unici oggetti rimasti intatti sono quelli nella lista che troverai qui sotto. Il tuo compito è ordinarli in base alla loro importanza per permettere al tuo equipaggio di raggiungere il punto di incontro. Più collocherai un oggetto in alto, maggiore sarà la sua importanza.")
    st.write("----------------")
    st.write("Tieni premuto un oggetto e trascinalo per ordinarlo.")

    items = []
    
    if(st.session_state.user_list == []):
        items = [
            {"id": 1, "name": "Scatola di Fiammiferi"},
            {"id": 2, "name": "Concentrato Alimentare"},
            {"id": 3, "name": "Corda in nylon di 15 metri"},
            {"id": 4, "name": "Paracadute di seta"},
            {"id": 5, "name": "Unità di Riscaldamento Portatile"},
            {"id": 6, "name": "Due pistole calibro .45"},
            {"id": 7, "name": "Latte disidratato"},
            {"id": 8, "name": "Bombole di ossigeno di 45kg"},
            {"id": 9, "name": "Mappa delle stelle"},
            {"id": 10, "name": "Zattera di salvataggio autogonfiabile"},
            {"id": 11, "name": "Bussola Magnetica"},
            {"id": 12, "name": "20 litri d'acqua"},
            {"id": 13, "name": "Razzo di segnalazione"},
            {"id": 14, "name": "Cassa di pronto soccorso"},
            {"id": 15, "name": "Radiolina alimentata con energia solare"}
        ]
    elif(st.session_state.user_list != []):
        items = st.session_state.user_list

    #lista con interazione
    draggable_list = DraggableList(items, key="draggable_list")
    st.write("-----------")
    st.write("Se hai terminato la classifica, puoi decidere se continuare individualmente o fare il prossimo passaggio insieme ad un'altra persona. In quest'ultimo caso premi sul pulsante ‘entra nella lobby', inserisci un username e manda una richiesta ad un altro utente collegato per iniziare una sessione collaborativa.")
    st.write ("----------------")
    main_col,spazio, right_col = st.columns([100,5,100])
    
    with main_col:
        if st.button("Continua individualmente"):
            st.session_state.user_list = draggable_list
            st.session_state.previous_list_text = "\n \n ".join([item['name'] for item in st.session_state.user_list])
            next_page()
    
    with right_col:
        if st.button("Entra nella lobby"):
            st.session_state.user_list = draggable_list
            st.session_state.previous_list_text = "\n \n ".join([item['name'] for item in st.session_state.user_list])
            st.session_state.page = 20
            st.rerun()
    st.components.v1.html("""
            <script>
                window.parent.document.getElementById('top').scrollIntoView({behavior: 'instant'});
            </script>
            """, height=0)
#-------------------------------------------------------------------------------------------------------------------------------------------------------------


#Lobby Utenti--------------------------------------------------------------------------------------------
elif(st.session_state.page == 20):
    
    st.title("Lobby utenti")
    
    while st.session_state.valid == "not valid":    

        username = st.text_input("Inserire un username:", key="username_input")
        st.session_state.username = username
        if not username:
            st.session_state.valid = "not valid"
            st.warning("Inserisci un username per entrare nella lobby.")
            if st.button("Indietro"):
                st.session_state.page = 3
                st.rerun()
                
            st.stop()

        utenti_collegati = fetch_connected_users()

        if username in utenti_collegati:
            st.warning(f"Il nome utente '{username}' è già utilizzato. Scegli un altro nome.")
            st.stop()
        else:
            st.session_state.valid = "valid"  
            st.session_state.username = username  
            break  
        
    st.session_state.valid = "not valid"
    username = st.session_state.username
    
    ws_code = f"""
        
    <script>
    const username = "{st.session_state.username}";
    
    var ws
    
    
    function connectToWebsocket(){{
        
        ws = new WebSocket("wss://eighty-groups-cut.loca.lt/ws/" + username);
        console.log("Provo a connettermi")
        
        ws.onopen = function() {{
            console.log("WebSocket connection established for " + username);
        }};
        
        ws.onerror = function(error){{
            console.error("WebSocket error: ", error);
            retryConnection(); 
        }}

        function retryConnection() {{
            const retryInterval = 3000;  // Retry every 3 seconds
            console.log("Attempting to reconnect in " + retryInterval / 1000 + " seconds...");
            setTimeout(connectToWebsocket, retryInterval);
        }}
        
        ws.onmessage = function(event) {{
            console.log("Received data:", event.data);
            const data = JSON.parse(event.data);

            if (data.type === 'user_list') {{
                console.log("Updating user list:", data.users);
                const userList = document.getElementById('userList');
                userList.innerHTML = "";  

                // Add the connected users to the dropdown
                data.users.forEach(user => {{
                    if (user !== username) {{
                        const option = document.createElement('option');
                        option.value = user;
                        option.textContent = user;
                        userList.appendChild(option);
                    }}
                }});
            }}
            
            if (data.type === 'request') {{
                const log = document.getElementById('log');

                // Create a new request container
                const requestId = 'request_' + data.fromUser;
                const requestContainer = document.createElement('div');
                requestContainer.id = requestId;
                requestContainer.innerHTML = `
                    <p>Richiesta da: ` + data.fromUser + `</p>
                    <button onclick="acceptRequest('` + data.fromUser + `')">Accetta</button>
                    <button onclick="refuseRequest('` + data.fromUser + `', '` + requestId + `')">Rifiuta</button>
                `;
                log.appendChild(requestContainer);  
            }}
            
            if (data.type === 'response' && data.response === 'accept') {{
                // When request is accepted, set redirect state and refresh the app
                console.log("Response received: ", data);
                const fromUser = data.fromUser;
                window.parent.postMessage({{ type: 'update_session_state', fromUser: fromUser }}, "*");
            }}
        }};
        
        
        }}
        
        function sendRequest() {{
            const toUser = document.getElementById('userList').value;
            if (toUser) {{
                ws.send(JSON.stringify({{ 'type': 'request', 'toUser': toUser }}));
                alert("Richiesta mandata all'utente " + toUser);
            }} else {{
                alert("Seleziona un utente a cui mandare la richiesta.");
            }}
        }}
        
        function acceptRequest(fromUser) {{
            ws.send(JSON.stringify({{ 'type': 'response', 'toUser': fromUser, 'fromUser': username, 'response': 'accept' }}));
            alert("Hai accettato la richiesta di " + fromUser);
        }}
        
        function refuseRequest(fromUser, requestId) {{
            ws.send(JSON.stringify({{ 'type': 'response', 'toUser': fromUser, 'response': 'refuse' }}));
            // Remove the request container from the DOM
            const requestContainer = document.getElementById(requestId);
            if (requestContainer) {{
                requestContainer.remove();
            }}
        }}
        
        connectToWebsocket();
</script>

<div style="font-family: Calibri, sans-serif; color: white; text-align: center; padding: 20px;">
        <h3 style="font-size: 24px;">Seleziona un utente a cui mandare la richiesta</h3>
        <select id="userList" style="font-size: 18px; padding: 5px; width: 200px; background-color: #f0f0f0; color: black; border: 1px solid black; border-radius: 5px;">
            <option value="" disabled selected>Seleziona un utente</option>
        </select>
        <br/><br/>
        <button id="confirmRequestButton" style="font-size: 18px; padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;" onclick="sendRequest()">Invia richiesta</button>
        <br/><br/>
        <div id="log"></div>  
    </div>
"""
    components.html(ws_code, height = 4000)
    st.write("---------")
    connected_users_placeholder = st.empty()
    chat_status_placeholder = st.empty()
    
    while st.session_state.page == 20:
        chat_partner = check_chat_partner(username)
        
        if chat_partner:
            st.session_state.partner = chat_partner
            chat_status_placeholder.empty()
            connected_users_placeholder.empty()
            previous_list = ", ".join([item['name'] for item in st.session_state.user_list])
            send_previous_list_to_backend(previous_list)
            next_page()

        time.sleep(5)
                    
#Pagina di ranking collaborativo-----------------------------------------------------------------------------------          
elif st.session_state.page == 21:
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.title("Ranking collaborativo con LLM")
    st.write(f"In questo momento sei collegato con l'utente {st.session_state.partner}. Qui sotto troverai una nuova lista (a sinistra) e la classifica che hai stilato individualmente (a destra). La lista di sinistra è condivisa con l’altro utente e le modifiche saranno visibili a entrambi. L'obiettivo è quello di collaborare per creare la classifica migliore (lo scenario è sempre quello del passo precedente: fate parte di un equipaggio sulla luna e dovete raggiungere l'astronave madre a 200km di distanza). Dovrai comunicare con {st.session_state.partner} utilizzando la chat. Durante la conversazione nella chat, interverrà il Large Language Model per dare la propria opinione, potete usare le risposte che fornirà come aiuto.")
    st.write("-----------")
    
    st_autorefresh(500)
    username = st.session_state.username
    
    if(st.session_state.modalita == ""):
        modalita = get_modalita()
        st.session_state.modalita = modalita
        print(f"MODALITA UTENTE {st.session_state.username}: {modalita}  ")
    
    colonna_sx, spazio, colonna_dx = st.columns([30, 10, 30]) 

    chatroom() 
     

    with colonna_sx:
        st.header("Lista collaborativa")
        new_list = get_shared_list()
        if(st.session_state.continua == True):
            st.session_state.updated_list = new_list
            ai_ranking = extract_ai_ranking(st.session_state.llm_response)

            st.session_state.ai_ranking = ai_ranking
            st.empty()
            st.session_state.page = 5
            st.rerun()
        draggable_key = generate_unique_key(username, new_list)
        if new_list != st.session_state.previous_list:

            st.session_state.previous_list = new_list  
            reordered_list = DraggableList(new_list, key=draggable_key)
        else:
            reordered_list = DraggableList(st.session_state.previous_list, key=draggable_key)

        if reordered_list != st.session_state.previous_list:
            st.session_state.previous_list = reordered_list
            send_list_to_backend(reordered_list)
    
    st.components.v1.html("""
            <script>
                window.parent.document.getElementById('top').scrollIntoView({behavior: 'instant'});
            </script>
            """, height=0)

    with colonna_dx:
        st.header("Lista individuale:")
        st.text_area( "", value=st.session_state.previous_list_text, height=680)
        
    st.write("----------------------------")
    
    if st.button("Conferma e prosegui"):
        ai_ranking = extract_ai_ranking(st.session_state.llm_response)
        st.session_state.ai_ranking = ai_ranking
        send_continua_message(st.session_state.username , st.session_state.partner)
        st.session_state.updated_list = new_list
        print(new_list)
        st.empty()
        st.session_state.page = 5
        st.rerun()
        
# Page 3: risposta ai ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
elif st.session_state.page == 4:
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    chat_with_model()
    
    user_ranked_list = ", ".join([item['name'] for item in st.session_state.user_list])
    messaggio_attesa = st.empty()
    st.title("Ranking con LLM")
    st.write("")
    st.write("Qua sotto troverai la tua classifica fatta al passo precedente (sulla sinistra) e la classifica secondo il modello di Intelligenza Artificiale (sulla destra). Puoi interagire con il LLM attraverso la chat per ottenere qualsiasi informazione (es: a cosa puo' servire un oggetto). In base a questi consigli puoi riordinare la lista. Quando hai finito, clicca su 'Conferma e prosegui' in fondo alla pagina per vedere i risultati.")
    st.write("-------------")
    st.components.v1.html("""
            <script>
                window.parent.document.getElementById('top').scrollIntoView({behavior: 'instant'});
            </script>
            """, height=0)
    main_col,spazio, right_col = st.columns([100,5, 100])  
    
    
    if(st.session_state.llm_response_generated == False):
        
        keyword = ""
        
        randomGenerator = random.seed(a=None , version=2 )
        tipoAI = random.randint(1,2)
        
        if(tipoAI == 1 ):
            keyword = "assertivo"
        elif(tipoAI == 2):
            keyword = "insicuro"
        print(keyword)
        
        st.session_state.keyword = keyword
        
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "L'utente è in una spedizione lunare"
                },
                {
                    "role": "user",
                    "content": f"Data la seguente lista di oggetti :\n{user_ranked_list}, "
                    "Ordina questi oggetti per importanza in una spedizione lunare. "
                    "L'output deve essere nella forma : 1. Nome Oggetto"
                    f"Devi spiegare brevemente, in italiano e in modo {keyword} perché gli oggetti sono ordinati in questo modo"
                }
            ],
            temperature=0.75,
            max_tokens=2048,
            top_p=1,
            stream=True,
            stop=None,
        )

        with right_col:

            response = ""
            for chunk in completion:
                response += chunk.choices[0].delta.content or ""
                
            st.text_area( "", value=response, height=620)
            st.session_state.llm_response = response
            st.session_state.llm_response_generated = True
            ai_ranking = extract_ai_ranking(st.session_state.llm_response)
            st.session_state.ai_ranking = ai_ranking
            messaggio_attesa.empty()

    else:
        with right_col:

            #response = example_response
            response = st.session_state.llm_response
            st.subheader("La classifica del LLM")
            st.text_area( "", value=response, height=620)
        
    
    with main_col:
        st.subheader("La tua classifica:")
        st.write("")
        st.write("")
        new_draggable_list = DraggableList(st.session_state.user_list, key="list")
        
    st.write("-----------")
    if(st.button("Conferma e prosegui")):
        st.session_state.updated_list = new_draggable_list 
        st.session_state.alone = True
        next_page()
    
# Page 4: Analisi Risultati ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

elif st.session_state.page == 5:
    
    # ranking NASA
    nasa_ranking = {
    "Scatola di Fiammiferi": 15,
    "Concentrato Alimentare": 4,
    "Corda in nylon di 15 metri": 6,
    "Paracadute di seta": 8,
    "Unità di Riscaldamento Portatile": 13,
    "Due pistole calibro .45": 11,
    "Latte disidratato": 12,
    "Bombole di ossigeno di 45kg": 1,
    "Mappa delle stelle": 3,
    "Zattera di salvataggio autogonfiabile": 9,
    "Bussola Magnetica": 14,
    "20 litri d'acqua": 2,
    "Razzo di segnalazione": 10,
    "Cassa di pronto soccorso": 7,
    "Radiolina alimentata con energia solare": 5
}

    #Dizionari dei vari ranking
    user_ranking = {item['name']: idx + 1 for idx, item in enumerate(st.session_state.user_list)}
    user_ranking_afterai = {item['name']: idx + 1 for idx, item in enumerate(st.session_state.updated_list)}
    
    ai_ranked_list = st.session_state.ai_ranking
    normalized_ai_ranks_dictionary = {}
    
    #Converto i ranking in una lista (contiene solo i valori dei ranking ordinati per tipo di item)
    nasa_ranks = []
    user_ranks = []
    user_ranks_afterai = []
    ai_ranks = []
    
    #Normalizzo gli item generati dall'AI (potrebbe dare un output con nomi di item leggermente diversi da quelli forniti)
    nasa_items = list(nasa_ranking.keys()) 
    
    
    #Creo il dizionario normalizzato
    for item in ai_ranked_list:
        rank = ai_ranked_list[item]
        normalized_name = get_best_match(item.lower().strip(), nasa_items)
        if normalized_name:
            normalized_ai_ranks_dictionary[normalized_name] = rank
         
    ai_ranks = ai_ranks[:15]
     
    #Aggiungo i rank ordinati nelle liste - le liste servono per calcolare lo spearman rank correlation
    for item in nasa_ranking.keys():
        nasa_ranks.append(nasa_ranking[item])
        user_ranks.append(user_ranking[item])
        user_ranks_afterai.append(user_ranking_afterai[item])
        if len(normalized_ai_ranks_dictionary) == 15:
            ai_ranks.append(normalized_ai_ranks_dictionary[item])


    #Calcolo il WoA (solo se l'output dell'IA ha fornito tutti e 15 gli oggetti)
    sum=0
    den=0
    if len(normalized_ai_ranks_dictionary) == 15:
        for i in range (0,14):
            initial = user_ranks[i]
            final = user_ranks_afterai[i]
            advice = ai_ranks[i]
            if(calculate_weight_of_advice(final,initial,advice) != None):
                sum += calculate_weight_of_advice(final,initial,advice)
                den += 1
        
    #spearman rank correlation
    spearman_corr, _ = stats.spearmanr(user_ranks, nasa_ranks)
    spearman_corr_afterai, _ = stats.spearmanr(user_ranks_afterai, nasa_ranks)
    if len(normalized_ai_ranks_dictionary) == 15:
        spearman_corr_ai, _ = stats.spearmanr(ai_ranks, nasa_ranks)
    
    
    st.title("RISULTATI")
    st.write("---")
    st.subheader("IMPORTANTE: per consegnare i risultati e concludere l'esperimento, vai in fondo alla pagina e clicca su 'Conferma e Termina'")
    st.write("---")
    st.write("Le tue classifiche sono state confrontate con la classifica ufficiale stilata dalla NASA. ")
    st.write("---")
    st.subheader("Metriche importanti:")
    st.write(f"Precisione classifica iniziale: {spearman_corr:.2f}")
    st.write(f"Precisione classifica finale: {spearman_corr_afterai:.2f}")
    
    if len(normalized_ai_ranks_dictionary) == 15:
        st.write(f"Precisione della classifica del LLM: {spearman_corr_ai:.2f}")
    if(den != 0):
        st.write(f"Weight of Advice : {round((sum/den),3)}")

    improvement_percentage = round(((spearman_corr_afterai - spearman_corr) / (1 - spearman_corr)) * 100 , 1)
    st.write("-------")
    if(improvement_percentage >= 0):
        st.subheader(f"Percentuale di miglioramento : {improvement_percentage}%")
        st.progress(improvement_percentage / 100)
    else:
        st.subheader(f"Percentuale di miglioramento : {improvement_percentage}%")
        st.progress(0)
    st.write("--------")
    df_ranking_comparison = pd.DataFrame({
    'Item': list(nasa_ranking.keys()),  #colonne con i nomi degli item
    'La tua lista iniziale': [user_ranking.get(item, None) for item in nasa_ranking.keys()],
    'La tua lista finale': [user_ranking_afterai.get(item, None) for item in nasa_ranking.keys()],  # metto il ranking utente nella stessa linea del ranking nasa
    'Lista ufficiale NASA':  [nasa_ranking.get(item,None) for item in nasa_ranking.keys()] # stessa cosa per la preciisone dopo intervento IA
        })
    
    
    styled_df = df_ranking_comparison.style.apply(highlight_closeness, axis=1)

    # mostro la tabella dei risultati
    st.subheader("Tabella di confronto dei risultati")
    st.write("La tabella mostra, per ogni oggetto, la posizione in classifica prima e dopo il consiglio del LLM e la posizione considerata corretta (in base alla classifica della NASA), gli oggetti che sono hanno avuto un miglioramento di precisione sono colorati in verde, quelli che hanno avuto un peggioramento sono colorati in rosso")
    st.table(styled_df)

    # confronto dei rankings
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df_ranking_comparison['Item']))
    ax.bar(x - 0.3, df_ranking_comparison['La tua lista iniziale'], width=0.2, label='La tua lista iniziale')
    ax.bar(x - 0.1, df_ranking_comparison['La tua lista finale'], width=0.2, label='La tua lista finale')
    ax.bar(x + 0.1, df_ranking_comparison['Lista ufficiale NASA'], width=0.2, label='Lista ufficiale NASA')
    ax.set_xticks(x)
    ax.set_xticklabels(df_ranking_comparison['Item'], rotation=45, ha='right')
    ax.set_ylabel('Ranking')
    ax.set_title('Comparison of User, AI, and NASA Rankings')
    ax.legend()

 
    #-------------------------------------------

    # Calcolo della precisione per ogni item
    max_rank_difference = 14

    # Accuracy per ogni item
    df_ranking_comparison['Accuracy_Iniziale'] = 1 - (abs(df_ranking_comparison['La tua lista iniziale'] - df_ranking_comparison['Lista ufficiale NASA']) / max_rank_difference)
    df_ranking_comparison['Accuracy_Finale'] = 1 - (abs(df_ranking_comparison['La tua lista finale'] - df_ranking_comparison['Lista ufficiale NASA']) / max_rank_difference)
    # Mostro l'accuracy per ogni item
    st.write("--------------------")
    st.subheader("Precisione di ogni oggetto, prima e dopo")
    st.write("Il grafico mostra, per ogni oggetto, la precisione nella classifica iniziale (before AI) e la precisione nella classifica finale (after AI)")
    # bar chart per confronto di precisione
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.bar(x - 0.2, df_ranking_comparison['Accuracy_Iniziale'], width=0.4, label='Precisione prima ', color='royalblue')
    ax2.bar(x + 0.2, df_ranking_comparison['Accuracy_Finale'], width=0.4, label='Precisione dopo', color='darkorange')

    # labels e legenda
    ax2.set_xlabel('Items')
    ax2.set_ylabel('Precisione')
    ax2.set_title('Confronto tra precisione : Before AI vs After AI')
    ax2.set_xticks(x)
    ax2.set_xticklabels(df_ranking_comparison['Item'], rotation=45,fontsize = 6)
    ax2.legend()

    # mostra il chart di precisione
    st.pyplot(fig2)


    with st.form("Ranking Form"):
        user_info = st.session_state.risposte_personali
        submit_button = st.form_submit_button(label='Conferma e termina')
        
    
    #Se clicco il bottone, invio tutti i risultati al database
    if(submit_button):
        if(st.session_state.alone == True):
            engine = get_engine_alone()
            session = get_session(engine)
            if(den != 0):
                insert_user_results_alone(session,round(spearman_corr,2) , round(spearman_corr_afterai,2) , improvement_percentage, st.session_state.keyword, round((sum/den),3))
            else:
                insert_user_results_alone(session,round(spearman_corr,2) , round(spearman_corr_afterai,2) , improvement_percentage, st.session_state.keyword,)
            insert_user_info_to_db(session, user_info["sesso"], user_info["eta"], user_info["professione"], user_info["esperienzaLLM"])
            insert_user_questions_to_db(session, st.session_state.risposte_questionario)
            next_page()
            
        if(st.session_state.alone == False):
            engine = get_engine()
            session = get_session(engine)
            
            if(den != 0):
                insert_user_results_to_db(session, round(spearman_corr,2) , round(spearman_corr_afterai,2) , improvement_percentage ,st.session_state.username,st.session_state.partner,st.session_state.modalita,round((sum/den),3))
            else:
                insert_user_results_to_db(session, round(spearman_corr,2) , round(spearman_corr_afterai,2) , improvement_percentage, st.session_state.username,st.session_state.partner,st.session_state.modalita)
            
            insert_user_info_to_db(session, user_info["sesso"], user_info["eta"], user_info["professione"], user_info["esperienzaLLM"])
            insert_user_questions_to_db(session, st.session_state.risposte_questionario)
            next_page()

        
elif st.session_state.page == 6:
    st.title("Grazie per aver partecipato")