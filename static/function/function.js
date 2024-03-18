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
// id='message_" + messageId + "'><b>" + username + "</b>: " + message + "</div></br>
function addMessage(messageJSON) {
    const chatMessages = document.getElementById("chatMessage");
    const username = messageJSON.username;
    const message = messageJSON.message;
    const like = messageJSON.likeCount
    const messageId = messageJSON.id;
    let messageHTML = "";
    messageHTML += "<div class='chat-message' value="+messageId +">\
                        <div class='username'>"+username+"</div>\
                        <div class='content'>"+message+"</div>\
                        <button class='like-button'>👍"+like+"</button>\
                    </div>";
    chatMessages.innerHTML += messageHTML;
}
function clearChat() {
    const chatMessages = document.getElementById("chatMessage");
    chatMessages.innerHTML = "";
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

setInterval(chatRequest, 1000);





