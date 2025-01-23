import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict,Tuple
from threading import Lock
import random
from groq import Groq
from apikey import GROQ_API_KEY
def set_modes(utente1,utente2,key):
    modo = ""
    utente = ""
    frase =  ""
    
    rand1 = random.randint(1,2)
    if(rand1 == 1):
        modo = "disaccordo"
        frase = "sta sbagliando l'utente"
    else:
        modo = "accordo"
        frase = "concordi con l'utente"
        
        
    rand2 = random.randint(1,2)
    if(rand2 == 1):
        utente = utente1
    else:
        utente = utente2
        
    manager.shared_modes[key] = [modo,utente]


def ask_llm(messages,modo,utente):
    
    conversazione = "\n".join(messages)
    print("Parametri dell'intervento llm : " + conversazione + str(modo) + str(utente))
    
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": 
                                    "Ogni utente ha stilato una classifica dei 15 oggetti più importanti per la sopravvivenza sulla luna, adesso stanno parlando per mettersi d'accordo"
                                    "Questa è la lista degli oggetti che hanno a disposizione (non sono ancora ordinati):"
                                    "Concentrato Alimentare"
                                    "Corda in nylon di 15 metri"
                                    "Paracadute di seta"
                                    "Unità di Riscaldamento Portatile"
                                    "Due pistole calibro .45"
                                    "Latte disidratato"
                                    "Bombole di ossigeno di 45kg"
                                    "Mappa delle stelle"
                                    "Zattera di salvataggio autogonfiabile"
                                    "Bussola Magnetica"
                                    "20 litri d'acqua"
                                    "Razzo di segnalazione"
                                    "Cassa di pronto soccorso"
                                    "Radiolina alimentata con energia solare"
                                    "Sei un assistente in " + str(modo) + "con l'utente " + str(utente) + ", ma non dirlo esplicitamente."
                    },
                    {
                        "role": "user",
                        "content": conversazione
                    }
                ],
                temperature=0.75,
                max_tokens=2048,
                top_p=1,
                stream=True,
                stop=None,
            )
            
    response = ""
    for chunk in completion:
            response += chunk.choices[0].delta.content or ""
    
    
    return f"LLM : '{response}'" 



def initial_llm_query(utente1, utente2, list1 , list2):
    key = tuple(sorted((utente1,utente2)))
    print("DATI INITIAL LLM QUERY : " + str(utente1) + " " + str(utente2) + " " + str(list1) + " " + str(list2))

    modo = manager.shared_modes[key][0]
    utente = manager.shared_modes[key][1]
    
    if modo == "disaccordo":
        frase = "sta sbagliando l'utente"
    else:
        frase = "concordi con l'utente"
        
        
        
    
    print("MODALITA'" + modo + utente)
    manager.shared_modes[key] = [modo,utente]
        
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
    model="llama3-70b-8192",
    messages=[
        {
            "role": "system",
            "content": (
                "Sei un assistente che analizza le classifiche fornite da due utenti. "
                "Gli utenti hanno stilato le classifiche degli oggetti fondamentali per la sopravvivenza sulla luna"
                "Sei in " + modo + "con l'utente " + utente + "."
                "Confronta le due classifiche e dì quello che " + frase + "."
                
               
            )
        },
        {
            "role": "user",
            "content": "Questa è la classifica dell'utente" + str(utente1) + ":" + str(list1)
        },
        {
            "role": "user",
            "content": "Questa è la classifica dell'utente" + str(utente2) + ":" + str(list2)
        }
    ],
    temperature=0.75,  
    top_p=1, 
    frequency_penalty=0.5,  
    presence_penalty=0.2,  
    stream=True,
    stop=None,
)
            
    response = ""
    for chunk in completion:
            response += chunk.choices[0].delta.content or ""
    
    

    return f"LLM : '{response}'"

origins = [
    "http://localhost:8501",  # Streamlit app origin
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

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
class ChatPartnerRequest(BaseModel):
    username: str
    chat_partner: str

class UpdateListRequest(BaseModel):
    username: str
    partner:str
    updated_list: list
    
class Message(BaseModel):
    from_user: str
    to_user: str
    content: str
    
class Confirm(BaseModel):
    user1: str
    user2: str
            
class ConnectionManager:
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connected_users: List[str] = []
        self.chat_partners = {}
        self.usernames = {}
        self.lock = Lock()
        self.shared_lists: Dict[Tuple[str, str], List[str]] = {}
        self.shared_lengths: Dict[Tuple[str,str] , List[int]] = {}
        self.previous_lists: Dict[Tuple[str,str], List[str]] = {}
        self.shared_modes: Dict[Tuple[str,str], List[str]] = {}
        self.connections = {}
        self.chat_storage: Dict[str, List[str]] = {}
    
        self.conferma: Dict[Tuple[str,str], bool] = {} 
        
    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()

    def disconnect(self, websocket: WebSocket, username: str):
            self.active_connections.remove(websocket)
            self.connected_users.remove(username)
            del self.usernames[username]
            
    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_user_list(self):
        message =  {
        "type": "user_list",
        "users": manager.connected_users
    }
        await self.broadcast(json.dumps(message))
        
    async def send_request(self, to_username: str, from_username: str):
        for username, websocket in self.usernames.items():
            if username == to_username:
                await websocket.send_text(f'{{"type": "request", "fromUser": "{from_username}"}}')
    
manager = ConnectionManager()

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):

    await manager.connect(websocket, username)
    if(username not in manager.connected_users):
        manager.active_connections.append(websocket)
        manager.connected_users.append(username)
        manager.usernames[username] = websocket
        await manager.broadcast_user_list()

    try:
        while True:
            data = await websocket.receive_text()
            message = eval(data) 
                
            if message['type'] == 'request': 
                await manager.send_request(message['toUser'] , username) 
                 
            elif message['type'] == 'response':
                if message['response'] == 'accept':
                    to_user = message['toUser']
                    from_user = message['fromUser']
                    
                    manager.chat_partners[from_user] = to_user
                    manager.chat_partners[to_user] = from_user
                    
                    key = tuple(sorted((from_user, to_user))) 
                    keychat = f"{to_user}-{from_user}" if to_user < from_user else f"{from_user}-{to_user}"

                    with manager.lock:
                        manager.shared_lists[key] = items 
                        manager.shared_lengths[key] = [0,0]
                        manager.chat_storage[keychat] = []
                        manager.previous_lists[key] = ["" , ""]
                        manager.conferma[key] = False
                        set_modes(from_user,to_user,key)
                        print(f"Messa la chiave a : {manager.conferma[key]}")
                    
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)
        await manager.broadcast_user_list()
        


@app.get("/connected_users")
async def get_connected_users():
    return manager.connected_users


@app.get("/get_chat_partner/{username}")
async def get_chat_partner(username: str):
    if username in manager.chat_partners.keys():
        return {"chat_partner": manager.chat_partners[username]}
    else:
        return {"chat_partner": None}
    
    
@app.get("/get_shared_list/{username}")
async def get_shared_list(username:str):
    partner = manager.chat_partners[username]
    key = tuple(sorted((username,partner)))
    if(key not in manager.conferma.keys()):
        print("Eccola, non trovo la chiave")
    if(key in manager.shared_lists.keys()):
        return {"lista": manager.shared_lists[key], "status": manager.conferma[key]}
    
    
@app.get("/get_messages/{user1}/{user2}")
async def get_messages(user1: str, user2: str):
    chat_key = f"{user1}-{user2}" if user1 < user2 else f"{user2}-{user1}"
    messages = manager.chat_storage.get(chat_key, [])
    return {"messages": messages}


@app.post("/api/update_list")
async def update_list(request: UpdateListRequest):
    pair_key = tuple(sorted((request.username, request.partner)))
    with manager.lock:  
        if pair_key in manager.shared_lists:
            manager.shared_lists[pair_key] = request.updated_list


@app.post("/send_message")
async def send_message(message: Message):
    chat_key = f"{message.from_user}-{message.to_user}" if message.from_user < message.to_user else f"{message.to_user}-{message.from_user}"
    key = tuple(sorted((message.from_user,message.to_user)))
    
    if chat_key not in manager.chat_storage:
        manager.chat_storage[chat_key] = []
        
    manager.chat_storage[chat_key].append(f"{message.from_user}: {message.content}")
    
    old_length = manager.shared_lengths[key][0]
    manager.shared_lengths[key][1] = len(manager.chat_storage[chat_key])
    new_length = manager.shared_lengths[key][1]
    
    if(new_length - old_length >= 3):
        manager.shared_lengths[key][0] = new_length
        modo = manager.shared_modes[key][0]
        utente = manager.shared_modes[key][1]
        latest_messages = []
        for i in range (old_length+1 , new_length):
            print(f"{i} : {manager.chat_storage[chat_key][i]}")
            latest_messages.append(manager.chat_storage[chat_key][i])
            print(latest_messages)
        llm_response = ask_llm(latest_messages, modo, utente)
        manager.chat_storage[chat_key].append(llm_response)
         
 
    print(f"Lunghezza lista = {manager.shared_lengths[key]}")

    return {"status": "Message sent"}
        

@app.post("/aggiorna_conferma")
async def update_status(request: Confirm):
    key = tuple(sorted((request.user1,request.user2)))
    manager.conferma[key] = True
    return {"status": "Conferma aggiornata"}



@app.post("/risposta_llm")
async def risposta_llm(message : Message):
    chat_key = f"{message.from_user}-{message.to_user}" if message.from_user < message.to_user else f"{message.to_user}-{message.from_user}"
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "L'utente è in una missione di sopravvivenza lunare"
                    },
                    {
                        "role": "user",
                        "content": message.content + " ,rispondi medio-brevemente in italiano"
                    }
                ],
                temperature=0.75,
                max_tokens=2048,
                top_p=1,
                stream=True,
                stop=None,
            )
            
    response = ""
    for chunk in completion:
            response += chunk.choices[0].delta.content or ""
        
    if chat_key not in manager.chat_storage:
        manager.chat_storage[chat_key] = []
    manager.chat_storage[chat_key].append(f"{message.from_user} : {message.content}")
    manager.chat_storage[chat_key].append(f"LLM: {response}")
            
    return "Completato" 
    
    
@app.post("/api/previous_list")
async def previous_list(request: UpdateListRequest):
    index = 0
    pair_key = tuple(sorted((request.username, request.partner)))
    chat_key = f"{request.username}-{request.partner}" if request.username < request.partner else f"{request.partner}-{request.username}"
    
    if(request.username > request.partner):
        index = 1 
    with manager.lock:
        if pair_key not in manager.previous_lists.keys():
            print("Errore : non ho inserito la chiave in previous lists")
        else:
            manager.previous_lists[pair_key][index] = request.updated_list
            print(manager.previous_lists[pair_key])
            
            if(manager.previous_lists[pair_key][abs(index-1)] != ""):   #SE ENTRAMBI HANNO INVIATO LE LISTE PRECEDENTI
                response = initial_llm_query(pair_key[0], pair_key[1] , manager.previous_lists[pair_key][0] , manager.previous_lists[pair_key][1] )
                if(chat_key not in manager.chat_storage.keys()):
                    manager.chat_storage[chat_key] = []
                manager.chat_storage[chat_key].append(response)
                
                
@app.get("/get_modalita/{username}/{partner}")
async def get_modalita(username: str, partner:str):
    key = tuple(sorted((username,partner)))
    utente = manager.shared_modes[key][1]
    modalita = manager.shared_modes[key][0]
    if(utente == username):
        return {"modalita" : modalita}
    else:
        return {"modalita" : "nessuna"}
        

