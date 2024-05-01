/*let socket = io.connect(`https://tbd312.me/`, {transports: ['websocket']});*/
let socket = io();


function submitPost() {
    const messageInput = document.getElementById('message');
    const imageInput = document.getElementById('image-upload');
    const message = messageInput.value;
    const imageFiles = imageInput.files;
    if (message.length > 2000) {
        alert("Maximum characters allowed are 2000.");
        return;
    }
    if (imageFiles && imageFiles.length > 0) {
        const imageFile = imageFiles[0];
        if ((imageFile.size/ 1024 / 1024) > 3){
            alert("Maximum file Upload size is 3MB");
            return;
        }
        const reader = new FileReader();
        reader.onload = function(event) {
            const imageData = event.target.result;
            const data = {
                message: message,
                image: imageData
            };
            console.log(data);
            socket.emit('blogMessage',data);
        };
        reader.readAsDataURL(imageFile);
        }
    else{
        const data = {
            message: message
        };
        socket.emit('blogMessage',data);
        }
    

    // Reset input values after submission
    messageInput.value = '';
    imageInput.value = '';
}




socket.on('connect_user',function(data){
    user = document.getElementById('userlist_'+data.email);
    if(user){
        user.remove();
    }
    addUser(data);
});


socket.on('UpdateTimer', function(data) {
    var Timer = document.getElementById('Time_' + data.email);
    if (Timer){
        var seconds = parseInt(data.seconds, 10);
        var hours = Math.floor(seconds / 3600);
        seconds = (seconds - (hours * 3600))
        var minutes = Math.floor(seconds / 60);
        seconds = (seconds - (minutes * 60))

        if (seconds < 10){
            seconds = "0"+String(seconds);
        }
        if (hours < 10){
            hours = "0"+String(hours);
        }
        if (minutes < 10){
            minutes = "0"+String(minutes);
        }
        Timer.innerHTML = `${hours}:${minutes}:${seconds}`;
    }
});


function addUser(data){
    const userlist = document.getElementById('online_users');
    if (userlist){
        let user = `<div class="user-picture-container" id=userlist_${data.email}>
                    <div class="user-info">
                        <div class="user-circle" id="blog-circle">
                            <img src=${data.ppicture}  alt="Profile Picture" >
                        </div>
                        <div class='username'>${data.username}</div>
                        <div id=Time_${data.email} class='Timer'>0 second</div>
                    </div>
                 </div>`;
        userlist.innerHTML += user;
    }
}

socket.on('disconnect_user',function(data){
    user = document.getElementById('userlist_'+data.email);
    if(user){
        user.remove();
    }

});

socket.on('NewMsg',function(data){
    addMessage(data);
});

function addMessage(messageJSON) {
    const chatMessages = document.getElementById("chatMessage");
    let messageHTML = `<div class='chat-message' id="Message_${messageJSON.id}">
                            <div class=".blog-picture-container">
                                <div class="blog-circle" id="blog-circle">
                                    <img src=${messageJSON.profile_picture}  alt="Profile Picture" >
                                </div>
                                <div class='username'>${messageJSON.username}</div>
                            </div>
                            <div id='msg_${messageJSON.id}' class='content'>${messageJSON.message}</div>
                            <div class = "blog-buttons-container"> 
                                <button id="Likebutton_${messageJSON.id}" onclick="likePost('${messageJSON.id}')" class='like-button'>👍 ${messageJSON.likeCount}</button>
                            `;
    if (messageJSON.imagePath !== ''){
        messageHTML = `<div class='chat-message' id="Message_${messageJSON.id}">
                                <div class=".blog-picture-container">
                                    <div class="blog-circle" id="blog-circle">
                                        <img src=${messageJSON.profile_picture}  alt="Profile Picture" >
                                    </div>
                                    <div class='username'>${messageJSON.username}</div>
                                </div>
                                <div id='msg_${messageJSON.id}' class='content'>${messageJSON.message}</div>
                                <span id='message_${messageJSON.id}'><img class= 'blog-image' src="${messageJSON.imagePath}"></span><br>
                                <div class = "blog-buttons-container"> 
                                    <button id="Likebutton_${messageJSON.id}" class="like-button" onclick="likePost('${messageJSON.id}')">👍 ${messageJSON.likeCount}</button>

                                `;
        }                        
    if (messageJSON.edit_permission === 'True'){
        messageHTML += `<button class='delete-button' onclick='deleteMessage("${messageJSON.id}")'>Delete</button>
                        <button id='button_${messageJSON.id}' class='edit-button' onclick='updateMessage("${messageJSON.id}")'>Edit</button>`;
    }
    messageHTML += '</div></div>';
    chatMessages.innerHTML = messageHTML + chatMessages.innerHTML;
}


function likePost(messageId) {
    const data = {
            message_id: messageId,
    };
    socket.emit('Like_Post',data);
}

socket.on('Like_Post',function(data){
    if (data.auth == 'error'){
        alert('Log in is required to like the post');
        return;
    }
    Likebutton = document.getElementById('Likebutton_'+data.message_id);
    Likebutton.innerHTML = '👍 '+data.likeCount;
    
});

function clearChat() {
    const chatMessages = document.getElementById("chatMessage");
    chatMessages.innerHTML = "";
}

function clearUserList(){
    const userlist = document.getElementById("online_users");
    if (userlist){
        userlist.innerHTML = "";
    }
}

function deleteMessage(messageId){
    const data = {
        message_id: messageId,
    };
    socket.emit('Delete_Post',data);
}

socket.on('Delete_Post',function(data){
    Message = document.getElementById('Message_'+data.message_id);
    Message.remove();
});

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
            const box = document.getElementById('msg_' + messageId);
            const message = box.value;
            const data = {
                message_id: messageId,
                update_message: message
            };
            socket.emit('Update_Post',data);

            const text = document.createElement('div');
            text.id = 'msg_' + messageId;
            text.classList.add('content');
            box.replaceWith(text);
            const updatebutton = document.getElementById('button_' + messageId)
            const editbutton = document.createElement('button');
            editbutton.textContent = 'Edit';
            editbutton.classList.add('edit-button');
            editbutton.id = 'button_' + messageId;
            editbutton.onclick = function() {
                updateMessage(messageId);
            };
            updatebutton.replaceWith(editbutton)
        }
        edit.replaceWith(update);
        };
        
    }

socket.on('Update_Post',function(data){
    Message = document.getElementById('msg_'+data.message_id);
    Message.innerHTML = data.message;
});

function chatRequest(){
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const messages = JSON.parse(this.response);
            clearChat();
            for (const message of messages) {
                addMessage(message);
            }
        }
    }
    request.open("GET", "/chat"); 
    request.send();
}

function userRequest(){
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const messages = JSON.parse(this.response);
            console.log(messages);
            clearUserList();
            for (const message of messages) {
                addUser(message);
            }
        }
    }
    request.open("GET", "/user_list"); 
    request.send();
}

chatRequest();
userRequest();




