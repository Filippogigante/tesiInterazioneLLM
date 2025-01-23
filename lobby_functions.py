import streamlit as st
import requests,uuid,hashlib
import streamlit.components.v1 as components 
from streamlit_autorefresh import st_autorefresh
from backend import ConnectionManager, websocket_endpoint,get_connected_users
import os, random, re, threading, time, json,copy
import streamlit as st # type: ignore
from gpt4all import GPT4All # type: ignore
from st_draggable_list import DraggableList # type: ignore
import numpy as np # type: ignore
import pandas as pd # type: ignore
import scipy.stats as stats # type: ignore
from fuzzywuzzy import process # type: ignore
import matplotlib.pyplot as plt #type:ignore
from database import get_engine, get_session, insert_user_results_to_db,insert_user_info_to_db, UserResults, UserInfo;
import asyncio
from groq import Groq #type:ignore
import websockets #type:ignore
from apikey import GROQ_API_KEY
#------------------------
BASE_URL = "http://127.0.0.1:8000"

def next_page():
    
    st.session_state.page += 1
    st.rerun()

def prev_page():
    if st.session_state.page > 1:
        st.session_state.page -= 1
        st.rerun()
        
def get_shared_list():
    response = requests.get(f'http://127.0.0.1:8000/get_shared_list/{st.session_state.username}')
    if response.status_code == 200:
        data = response.json()

        if(data['status'] == True):
            st.session_state.continua = True
        return data['lista']
    else:
        return None

def send_message():
    paired_user = st.session_state.partner
    user_input = st.session_state.chat_input
    username = st.session_state.username
    if user_input != st.session_state.last_user_input:
            st.session_state.chat_input = ""
            st.session_state.last_user_input = user_input
            response = requests.post(f"{BASE_URL}/send_message", json={
                "from_user": username,
                "to_user": paired_user,
                "content": user_input
            })
            #st.session_state.chat_input = ""
            if response.status_code != 200:
                print("Errore nell'invio del messaggio")
    else:
        st.session_state.chat_input = ""
                
      
def chatroom():
    user_compagno = st.session_state.partner
    username = st.session_state.username
    #prev_number = st.session_state.lunghezza_messaggi_prima
    #numero_messaggi = len(st.session_state.messages)
    
    #if(numero_messaggi - prev_number) >= 2:
    #    st.session_state.lunghezza_messaggi_prima = numero_messaggi
    #    message_to_analyze = st.session_state.messages[prev_number:numero_messaggi]        
    #    send_llm_message_to_backend(message_to_analyze)
        
        
    st.sidebar.title(f"Chat Room | {username} & {user_compagno}")
   
    fetch_messages()    
    for msg in st.session_state.messages:
        st.sidebar.write(msg)
    
    
    if prompt := st.chat_input("Invia un messaggio in chat"):
        st.session_state.chat_input = prompt
        send_message()

def fetch_messages():
    user_compagno = st.session_state.partner
    username = st.session_state.username
    response = requests.get(f"{BASE_URL}/get_messages/{username}/{user_compagno}")
    if response.status_code == 200:
        all_messages = response.json().get("messages", [])
        st.session_state.messages = all_messages

def fetch_connected_users():
        try:
            response = requests.get("http://127.0.0.1:8000/connected_users")
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error: Received status code {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred while fetching connected users: {e}")
            return []

def check_chat_partner(username):
    response = requests.get(f'http://127.0.0.1:8000/get_chat_partner/{username}')
    if response.status_code == 200:
        data = response.json()
        return data['chat_partner']
    else:
        return None

def send_list_to_backend(updated_list):

    url = "http://127.0.0.1:8000/api/update_list"  
    payload = {
        "username": st.session_state.username,
        "partner": st.session_state.partner,
        "updated_list": updated_list
    }
    
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            print("Lista inviata")
        else:
            print(f"Failed to send list. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while sending list: {e}")
             
def generate_unique_key(username, shared_list):
    
    list_representation = ','.join([str(item) for item in shared_list])
    
    list_hash = hashlib.sha256(list_representation.encode()).hexdigest()
    unique_key = f"{username}_{list_hash}"
    return unique_key

def send_continua_message(user1, user2):
    url = "http://127.0.0.1:8000/aggiorna_conferma"  
    payload = {
        "user1": user1,
        "user2": user2,
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data = json.dumps(payload), headers=headers)
        if response.status_code != 200:
            print(f"Errore nell'invio del messaggio di continuo")
    except requests.exceptions.RequestException as e:
        print("Errore nell'invio del messaggio di continuo")


def send_previous_list_to_backend(lista):
    
    url = "http://127.0.0.1:8000/api/previous_list"  
    payload = {
        "username": st.session_state.username,
        "partner": st.session_state.partner,
        "updated_list": [lista]
    }
    
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            print("Lista precedente inviata")
        else:
            print(f"Failed to send previous list. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while sending previous list: {e}")
    
    
    
def get_modalita():
    username = st.session_state.username
    partner = st.session_state.partner
    
    response = requests.get(f"http://127.0.0.1:8000/get_modalita/{username}/{partner}")
    
    if response.status_code == 200:
        data = response.json()
        return data['modalita']
    
        
        
        
        
        
        
        
#SOLO UNO DEI DUE DEVE MANDARE LA QUERY AL LLM