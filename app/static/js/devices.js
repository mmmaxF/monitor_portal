document.addEventListener("DOMContentLoaded", function () {
    // =========================
    // 削除確認
    // =========================
    const deleteForms = document.querySelectorAll(".delete-form");

    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const button = form.querySelector(".delete-button");
            const deviceName = button?.dataset?.deviceName || "この機器";

            const ok = window.confirm(`${deviceName} を削除してよろしいですか？`);

            if (!ok) {
                event.preventDefault();
            }
        });
    });

    // =========================
    // CSVファイル簡易チェック
    // =========================
    const fileInputs = document.querySelectorAll('input[type="file"]');

    fileInputs.forEach(function (input) {
        input.addEventListener("change", function () {
            const file = input.files && input.files[0];

            if (!file) {
                return;
            }

            if (!file.name.toLowerCase().endsWith(".csv")) {
                window.alert("CSVファイルを選択してください。");
                input.value = "";
            }
        });
    });

    // =========================
    // 編集モーダル
    // =========================
    const modal = document.getElementById("editModal");
    const editForm = document.getElementById("editForm");

    const editHostname = document.getElementById("editHostname");
    const editIpAddress = document.getElementById("editIpAddress");
    const editSubnet = document.getElementById("editSubnet");
    const editRole = document.getElementById("editRole");
    const editMemo = document.getElementById("editMemo");

    const editButtons = document.querySelectorAll(".edit-button");

    function openModal() {
        modal.classList.remove("hidden");
    }

    function closeModal() {
        modal.classList.add("hidden");
    }

    editButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const deviceId = button.dataset.deviceId;

            editForm.action = `/ui/devices/update/${deviceId}`;

            editHostname.value = button.dataset.hostname || "";
            editIpAddress.value = button.dataset.ipAddress || "";
            editSubnet.value = button.dataset.subnet || "";
            editRole.value = button.dataset.role || "";
            editMemo.value = button.dataset.memo || "";

            openModal();
        });
    });

    const closeButtons = document.querySelectorAll("[data-close-modal='true']");

    closeButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            closeModal();
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeModal();
        }
    });
});