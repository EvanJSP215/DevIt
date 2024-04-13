const ws = true;
let socket = null;

function initWS(){
    if(ws){
        socket = new WebSocket('ws://' + window.location.host + '/websocket');

        socket.onmessage = function(ws_message) {
            /* json format 
                'messageType': 'blogMessage (or the type you want to add)', 
                'username': username/email of the sender, 
                'message': html escaped message submitted by user, 
                'id': id_of_the_message,
                'likeCount': like count, 
                'edit_permission': edit, 
                'imagePath' : image path of post (can be empty if the post does not have an image), 
                'profile_picture': profile pic path
            */
            const data = JSON.parse(ws_message.data);
            const messageType = data.messageType;
            if (messageType === 'blogMessage') {
                addMessage(message);
            } //to handle more types add message type
        };
    }
}

function submitPost() {
    const messageInput = document.getElementById('message');
    const imageInput = document.getElementById('image-upload');

    const message = messageInput.value;
    const imageFile = imageInput.files[0];

    if (socket.readyState === WebSocket.OPEN) {
        if (imageFile) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const imageData = event.target.result;
                const data = {
                    messageType: 'blogMessage',
                    message: message,
                    image: imageData
                };
                socket.send(JSON.stringify(data));
            };
            reader.readAsDataURL(imageFile);
        }else{
            const data = {
                messageType: 'blogMessage',
                message: message,
                image: ''
            };
            socket.send(JSON.stringify(data));
        }
    }else{
        console.error('WebSocket connection not open.');
    }

    // Reset input values after submission
    messageInput.value = '';
    imageInput.value = '';
}

function addMessage(messageJSON) {
    const chatMessages = document.getElementById("chatMessage");
    let messageHTML = `<div class='chat-message' value=${messageJSON.id}>
                            <div class=".blog-picture-container">
                                <div class="blog-circle" id="blog-circle">
                                    <img src=${messageJSON.profile_picture}  alt="Profile Picture" >
                                </div>
                                <div class='username'>${messageJSON.username}</div>
                            </div>
                            <div id='msg_${messageJSON.id}' class='content'>${messageJSON.message}</div>
                            <div class = "blog-buttons-container"> 
                                <button onclick="likePost('${messageJSON.id}')" class='like-button'>👍 ${messageJSON.likeCount}</button>
                            `;
    if (messageJSON.imagePath !== ''){
       messageHTML = `<div class='chat-message' value=${messageJSON.id}>
                            <div class=".blog-picture-container">
                                <div class="blog-circle" id="blog-circle">
                                    <img src=${messageJSON.profile_picture}  alt="Profile Picture" >
                                </div>
                                <div class='username'>${messageJSON.username}</div>
                            </div>
                            <div id='msg_${messageJSON.id}' class='content'>${messageJSON.message}</div>
                            <span id='message_${messageJSON.id}'><img class= 'blog-image' src="${messageJSON.imagePath}"></span><br>
                            <div class = "blog-buttons-container"> 
                                <button onclick="likePost('${messageJSON.id}')" class='like-button'>👍 ${messageJSON.likeCount}</button>
                            `;
    }                        
    if (messageJSON.edit_permission === 'True'){
        messageHTML += `<button class='delete-button' onclick='deleteMessage("${messageJSON.id}")'>Delete</button>
                        <button id='button_${messageJSON.id}' class='edit-button' onclick='updateMessage("${messageJSON.id}")'>Edit</button>`;
    }
    messageHTML += '</div></div>';
    chatMessages.innerHTML += messageHTML;
}

function likePost(messageId) {
    fetch(`/like/${messageId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                chatRequest(); // Call chatRequest to refresh the messages and their like counts
            }
        })
        .catch(error => console.error('Error liking the post:', error));
}


function clearChat() {
    const chatMessages = document.getElementById("chatMessage");
    chatMessages.innerHTML = "";
}

function deleteMessage(messageId){
    const delete_request = new XMLHttpRequest();
    delete_request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    delete_request.open("DELETE", "/chat/" + messageId);
    delete_request.send();
}

function updateMessage(messageId) {
    const message = document.getElementById('msg_' + messageId);
    if (message) {
        const textinput = document.createElement('textarea');
        textinput.value = message.textContent;
        textinput.cols = 80;
        textinput.id = 'msg_' + messageId;
        message.replaceWith(textinput);
        /* Replace edit button with update */
        const edit = document.getElementById('button_' + messageId);
        const update = document.createElement('button');
        update.textContent = 'Update';
        update.classList.add('edit-button');
        update.id = 'button_' + messageId;
        update.onclick = function(){
            const update_request = new XMLHttpRequest();
            update_request.onreadystatechange = function () {
            if (this.readyState === 4 && this.status === 200) {
                    console.log(this.response);}
            }
            const box = document.getElementById('msg_' + messageId);
            update_request.open("PUT", "/chat/" + messageId);
            const message = box.value;
            update_request.setRequestHeader("Content-Type", "application/json");
            update_request.send(JSON.stringify({ "message": message }));
            const text = document.createElement('div');
            text.id = 'msg_' + messageId;
            text.classList.add('content');
            box.replaceWith(text);
            const updatebutton = document.getElementById('button_' + messageId)
            const editbutton = document.createElement('button');
            editbutton.textContent = 'Edit';
            editbutton.classList.add('edit-button');
            editbutton = 'button_' + messageId;
            editbutton.onclick = "updateMessage(" + messageId + ")"
            updatebutton.replaceWith(editbutton)
        }
        edit.replaceWith(update);
        };
        
    }

function chatRequest(){
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const messages = JSON.parse(this.response);
            clearChat();
            for (const message of messages.reverse()) {
                addMessage(message);
            }
        }
    }
    request.open("GET", "/chat"); 
    request.send();
}

setInterval(chatRequest, 4000);


