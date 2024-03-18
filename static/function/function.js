function pwstrengthcheck(){
    var input = document.getElementById('reg-pass').value;
    var pwcheck = document.getElementById("pwstrength"); 

    if (input.length > 0) {
        pwcheck.style.display = "block";
        c1 = checkUpper(input);
        c2 = checklower(input);
        c3 = checkspecial(input);
        c4 = checknum(input);
        c5 = checklen(input);
        if (c1 && c2 && c3 && c4 && c5){
            return true;
        } else {
            return false;
        }
    } else {
        pwcheck.style.display = "none";
        return false;
    }
}


function checkUpper(pw){
    var up = document.getElementById('uppercase');
    if(/[A-Z]/.test(pw)){
        up.checked = true;
        return true;
    }
    else{
        up.checked = false;
        return false;
    }
}

function checklower(pw){
    var low = document.getElementById('lowercase');
    if(/[a-z]/.test(pw)){
        low.checked = true;
        return true;
    }
    else{
        low.checked = false;
        return false;
    }
}

function checkspecial(pw){
    var special = document.getElementById('specials');
    if(/[!@#$%^&*()_+{}\[\]:;<>,.?~\\/-='"]/.test(pw)){
        special.checked = true;
        return true;
    }
    else{
        special.checked = false;
        return false;
    }
}

function checknum(pw){
    var num = document.getElementById('numbers');
    
    if(/\d/.test(pw)){
        num.checked = true;
        return true;
    }
    else{
        num.checked = false;
        return false;
    }
}

function checklen(pw){
    var len = document.getElementById('length');
    if (pw.length >=8){
        len.checked = true;
        return true;
    }
    else{
        len.checked = false;
        return false;
    }
}

function regcheck(){
    pw = document.getElementById('reg-pass').value;
    cpw = document.getElementById('reg-cpass').value;
    email = document.getElementById('reg_email').value.toLowerCase();
    var feedback = document.getElementById("regfailed");
    if (!(pwstrengthcheck())){
        feedback.style.display = "block";
        feedback.textContent = 'Please Check the Password Requirement!';
        return false;
    }
}

function blogConfirm(){
}

function addMessage(messageJSON) {
    const chatMessages = document.getElementById("chatMessage");
    const username = messageJSON.username;
    const message = messageJSON.message;
    const like = messageJSON.likeCount
    const messageId = messageJSON.id;
    const permission = messageJSON.edit_permission;
    let messageHTML = "";
    messageHTML += "<div class='chat-message' value="+messageId +">\
                        <div class='username'>"+username+"</div>\
                        <div id='msg_" + messageId + "' class='content'>" + message + "</div>\
                        <button class='like-button'>👍"+like+"</button>\
                        ";
    if (permission === 'True'){
        messageHTML += "<button class='delete-button' onclick='deleteMessage(" + messageId + ")'>Delete</button>";
        messageHTML += "<button id='button_" + messageId + "' class='edit-button' onclick='updateMessage(" + messageId + ")'>Edit</button>";
    }
    messageHTML += '</div>';
    chatMessages.innerHTML += messageHTML;
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





