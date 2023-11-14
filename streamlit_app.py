import streamlit as st
import pandas as pd
import csv

from pytube import YouTube
import os
import openai
import whisper
import assemblyai as aai
import zipfile
import base64
aai.settings.api_key =  os.environ.get("ASSEMBLYAI_API_KEY")

openai.api_key= os.environ.get("openai")

def video_audio(link):
    if not link:
        raise ValueError("Error: YouTube link is empty. Please provide a valid YouTube link.")

    print("Processing YouTube link:", link)

    try:
        yt = YouTube(link)
        stream = yt.streams.filter(only_audio=True).first()

        # Download the audio stream
        stream.download()

        # Original file name
        original_file = stream.default_filename

        # Specify the desired file name for the saved audio
        desired_file_name = "video_audio.mp3"

        # Rename the file to the desired file name
        os.rename(original_file, desired_file_name)

        st.write("Audio generated")
        st.write("")
        st.write("Starting transcription, which may take additional time...")
        return desired_file_name

    except Exception as e:
        raise ValueError(f"Error processing YouTube link {link}: {e}")

def split_string_into_chunks(input_string, max_chunk_length=9000):
    if len(input_string) <= max_chunk_length:
        return [input_string]  # Return the string as a single element list

    chunks = []
    current_chunk = ""

    for char in input_string:
        if len(current_chunk) < max_chunk_length:
            current_chunk += char
        else:
            chunks.append(current_chunk)
            current_chunk = char

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def audio_to_text(link):
    audio=video_audio(link)
    with open(audio, 'rb') as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file)
    hindi=transcription['text']
    
    spl=split_string_into_chunks(hindi)
    english=" ".join([translator(i,"english") for i in spl])
    
    spl2=split_string_into_chunks(english)
    
    hashtg=" ".join([hashtag(i) for i in spl2])
    summ1=" ".join([abstract_summary_extraction(i) for i in spl2])
    
    summ2=" ".join([translator(i,"hindi") for i in split_string_into_chunks(summ1)])
    

    return hindi,english, summ1,summ2,hashtg, audio


def abstract_summary_extraction(transcription):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        
        st.write("Summary done!")
        return response['choices'][0]['message']['content']
    except openai.error.ServiceUnavailableError:
        st.write("Got openai error which says 'The server is overloaded or not ready yet.' Please try again after sometimes.")
        sys.exit("The OpenAI service is currently unavailable. Program terminated.")
        

def translator(transcription,lang):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a highly skilled AI trained in language translation. I would like you to translate the following text into {lang} language."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        st.write("")
        st.write("translation done!")
        return response['choices'][0]['message']['content']
    except openai.error.ServiceUnavailableError:
        st.write("Got openai error which says 'The server is overloaded or not ready yet.' Please try again after sometimes.")
        sys.exit("The OpenAI service is currently unavailable. Program terminated.")

def hashtag(transcription):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly skilled AI trained in social media. I would like you to create hashtags based on the content."
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]
        )
        st.write("")
        st.write("hashtag done!")
        return response['choices'][0]['message']['content']
    except openai.error.ServiceUnavailableError:
        st.write("Got openai error which says 'The server is overloaded or not ready yet.' Please try again after sometimes.")
        sys.exit("The OpenAI service is currently unavailable. Program terminated.")

def video_list(l):
    all_links=[]
    columns=["YouTube Link","Hindi","English","Summary","Hashtag"]
    csv_file = 'info.csv'
       
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        
    for i,j in enumerate(l):
        st.write("Proceeding for Link: ",i+1)
        a,b,c,d,e,f=audio_to_text(j)
        ff=[f"Link:{i} \n\n"+j,a,b,c,d,e]
        all_links.append(ff)
        en,hi=subtitle(f,i)
     # Append a single row to the CSV file
    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(all_links)
        
    return csv_file,en,hi
        

def subtitle(audio,i):
    
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio)
    
    # in SRT format
    a=transcript.export_subtitles_srt()
    filename=f"subtitle_{i}.srt"
    # Save the updated SRT content to a file
    with open(filename, "w") as file:
        file.write(a)
        
    with open(filename, 'r', encoding='utf-8') as file:
            srt_text = file.read()

    spl=split_string_into_chunks(srt_text)
    ab=" ".join([translator(i,"hindi") for i in spl])
    filename2=f"subtitle_hindi_{i}.srt"
    with open(filename2, "w") as file:
        file.write(ab)
    
    return filename,filename2

def zipping(files):
   
    zip_file_name = "my_archive.zip"
    st.write(f"{files}")
    print(files)
    # Create a new zip file
    with zipfile.ZipFile(zip_file_name, "w") as zipf:
        
        # Add the specified files to the zip archive
        for file_name in files:
            
            # The second argument to write should specify the archive name, not the entire path
            arcname = os.path.basename(file_name)
            zipf.write(file_name, arcname=arcname)

    return zip_file_name

def get_binary_file_downloader_html(bin_data, file_label='File'):
    bin_str = base64.b64encode(bin_data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}.zip">Click here to download {file_label}</a>'
    return href
    

def main():
    st.sidebar.header("API Keys")
    assemblyai_api_key = st.sidebar.text_input("Enter AssemblyAI API Key")
    openai_api_key = st.sidebar.text_input("Enter OpenAI API Key")

    # Set the API keys
    aai.settings.api_key = assemblyai_api_key
    openai.api_key = openai_api_key

    st.title("YouTube to doc")
    num_text_boxes = st.number_input("Number of links", min_value=1, step=1)
    text_boxes = []

    for i in range(num_text_boxes):
        text_boxes.append(st.text_input(f"YouTube Link: {i+1}"))

    if st.button('Send'):
        try:
            # Check if any link is empty
            if any(not link for link in text_boxes):
                raise ValueError("Error: YouTube link is empty. Please provide valid YouTube links.")

            csv_file, en, hi = video_list(text_boxes)
            finall = [csv_file, en, hi]
            zip_file_path = zipping(finall)

            with open(zip_file_path, 'rb') as f:
                st.download_button('Download Zip', f, file_name='archive.zip')

        except ValueError as ve:
            st.error(ve)

if __name__ == "__main__":
    main()
