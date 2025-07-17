const pluralMap = {
    therapist: "therapists-list",
    secretary: "secretaries-list",
    admin: "admins-list"
};

function approveUser(userId) {
    const role = document.getElementById(`role-${userId}`).value;
    const specialization = document.getElementById(`spec-${userId}`)?.value || "";

    if (!role) {
        alert("Please select a role before approving.");
        return;
    }

    fetch("/api/approve_user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user_id: userId,
            role: role,
            specialization: specialization
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const userItem = document.getElementById(`user-${userId}`);
            const name = userItem.querySelector("strong").innerText;
            const email = userItem.innerText.match(/\(([^)]+)\)/)[1];

            const listId = pluralMap[role];
            const targetList = document.getElementById(listId);

            if (!targetList) {
                alert(`Error: No list found for role "${role}"`);
                return;
            }

            const template = document.getElementById("user-template");
            const clone = template.content.cloneNode(true);
            const display = clone.querySelector(".user-display");
            const editLink = clone.querySelector(".edit-link");

            display.textContent = role === "therapist"
                ? `${name} — ${specialization} (${email})`
                : `${name} (${email})`;

            editLink.href = `/edit_user/${userId}`;

            const li = clone.querySelector("li");
            li.style.opacity = 0;
            li.style.transition = "opacity 0.4s ease-in";

            // Fade out pending entry
            userItem.style.transition = "opacity 0.4s ease-out";
            userItem.style.opacity = 0;

            setTimeout(() => {
                userItem.remove();
                targetList.appendChild(li);
                requestAnimationFrame(() => {
                    li.style.opacity = 1;
                });

                // Remove "no [role] yet" labels if present
                const labelId = `no-${role}s-label`;
                const label = document.getElementById(labelId);
                if (label) label.remove();
            }, 400);
        } else {
            alert("Error: " + data.error);
        }
    });
}

// ✅ Expose function globally so onclick="approveUser(...)" works
window.approveUser = approveUser;




function pollPendingUsers() {
    fetch("/api/pending_users")
        .then(res => res.json())
        .then(users => {
            const pendingList = document.getElementById("pending-users");
            const noLabel = document.getElementById("no-pending-label");

            // Track if any were added
            let newUserAdded = false;

            users.forEach(u => {
                if (!document.getElementById(`user-${u.id}`)) {
                    const li = document.createElement("li");
                    li.id = `user-${u.id}`;
                    li.innerHTML = `
                        <strong>${u.name}</strong> (${u.email})
                        <label>
                            Role:
                            <select id="role-${u.id}">
                                <option value="">-- Select --</option>
                                <option value="therapist">Therapist</option>
                                <option value="secretary">Secretary</option>
                                <option value="admin">Admin</option>
                            </select>
                        </label>
                        <span id="spec-container-${u.id}" style="display:none;">
                            <label>
                                Specialization:
                                <input type="text" id="spec-${u.id}" placeholder="e.g., CBT">
                            </label>
                        </span>
                        <button onclick="approveUser('${u.id}')">✅ Approve</button>
                    `;
                    pendingList.appendChild(li);
                    newUserAdded = true;

                    document.getElementById(`role-${u.id}`).addEventListener("change", e => {
                        const specField = document.getElementById(`spec-container-${u.id}`);
                        specField.style.display = e.target.value === "therapist" ? "inline" : "none";
                    });
                }
            });

            // Remove label if users appear
            if (users.length > 0 && noLabel) {
                noLabel.style.display = "none";
            }

            // Show label only if no users at all
            if (users.length === 0 && noLabel) {
                noLabel.style.display = "block";
            }
        });
}


// 🔁 Start polling every 10 seconds
setInterval(pollPendingUsers, 10000);

