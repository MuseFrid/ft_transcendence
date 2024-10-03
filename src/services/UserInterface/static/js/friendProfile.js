function findGoodUser(usernameSearching, response) {
    for (let i = 0; i < response.users.length; i++) {
        if (response.users[i].username === usernameSearching) {
            // console.log(response.users[i]);
            return (i);
        }
    }
}

function searchUser(usernameSearching) {
    console.log('debut search user');
    if (usernameSearching != "") {
        const userNameFriend = document.getElementById('userNameFriend');
        let url = "https://localhost:8001/game/search?page=1&query=sgodin&filter=user/game";
        url = url.replace("localhost", window.location.hostname);
        url = url.replace("sgodin", usernameSearching);
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.withCredentials = true;
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200 || xhr.status === 201) {
                    response = JSON.parse(xhr.responseText);
                    // console.log(response);
                    // console.log(response.users.length);
                    // if (response.users.length != 1) {
                    numUser = findGoodUser(usernameSearching, response);
                    // console.log(response.users[numUser]);
                    // console.log(userNameFriend);
                    var tmp = userNameFriend.textContent;
                    userNameFriend.innerHTML = response.users[numUser].username;
                    // console.log("innerHTML: " + userNameFriend.innerHTML);
                    userNameFriend.textContent = tmp.replace("test", response.users[numUser].username);
                    // console.log(userNameFriend.textContent);
                    // console.log(tmp);
                    // userNameFriend.textContent = tmp;
                    // userName.textContent = response.users[numUser].username;
                    // console.log(userName.textContent);
                    // console.log('fin search user');
                    loadProfilePicture(response.users[numUser].id);
                    loadHistoryFromUser(response.users[numUser].id);
                    // } else {
                    //     userName.textContent = response.users[0].username;
                    //     loadProfilePicture(response.users[0].id);
                    // }
                    // if (response.users.length == 1) {
                    //     load
                    //     loadHistoryFromUser(response.users[0].id);
                    // } else if (response.users.length > 0) {
                    //     let foundUser = response.users.find(users => users.username === searchValue.value);
                    //     if (foundUser)
                    //         loadHistoryFromUser(foundUser.id);
                    // }
                    // console.log(this.response);
                } else {
                    alert('Error: ' + JSON.parse(xhr.responseText).error);
                }
            }
        };
        xhr.send();
    }
}

function loadHistoryFromUser(id) {
    let url = "https://localhost:8001/game/hist?UserId={{UserId}}";
    url = url.replace("localhost", window.location.hostname);
    url = url.replace("{{UserId}}", id);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.withCredentials = true;
    xhr.onreadystatechange = function () {
        // console.log(xhr.readyState);
        if (xhr.readyState === 4) {
            if (xhr.status === 200 || xhr.status === 201) {
                response = JSON.parse(xhr.responseText);
                console.log(response);
                displayHistorique(response);
            } else {
                alert('Error: ' + JSON.parse(xhr.responseText).error);
            }
        }
    };
    xhr.send();
}

function displayHistorique(response) {
    const historySpace = document.getElementById('history');
    if (response.length == 0) {
        // no historique for the moment
        historySpace.innerHTML = "<p class=\"game\">no history for the moment<\/p>";
    }
    for (let i = 0; i < response.length; i++) {
        let date = response[i].start_date.substr(0, 10);
        let tmp = "<p class=\"game\">";
        console.log(response[i].win);
        if (response[i].win == true)
            tmp += "<a class=\"victory\" style=\"color: green;\">" + "Win" + "<\/a>"
        else
            tmp += "<a class=\"victory\" style=\"color: red;\">" + "Loose" + "<\/a>"
        tmp += "<a class=\"mode\">" + response[i].gameName + "<\/a>"
        tmp += "<a class=\"score\">" + response[i].scores + "<\/a>"
        tmp += "<a class=\"date\">" + date + "<\/a>"
        tmp += "<a class=\"status\">" + response[i].status + "<\/a>"
        // tmp += response[i].id + "  " + response[i].status + "  " + date + "  " + response[i].gameName;
        tmp += "<\/p>";
        historySpace.innerHTML += tmp;
    }
}

// retirer sur pas finish
// changer la couleur