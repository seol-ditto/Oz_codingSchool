/**
 * 유틸리티 함수 모음
 */

const utils = {
    showAlert(message, type = 'info', title = '알림') {
        const modal = document.getElementById('alert-modal');
        const iconEl = document.getElementById('alert-modal-icon');
        const titleEl = document.getElementById('alert-modal-title');
        const messageEl = document.getElementById('alert-modal-message');
        const closeBtn = document.getElementById('alert-modal-close-btn');

        if (!modal) {
            alert(message);
            return;
        }

        titleEl.innerText = title;
        messageEl.innerText = message;
        
        // 아이콘 설정
        iconEl.className = 'modal-icon ' + type;
        if (type === 'error') iconEl.innerText = '⚠️';
        else if (type === 'success') iconEl.innerText = '✅';
        else iconEl.innerText = 'ℹ️';

        modal.classList.add('show');

        return new Promise((resolve) => {
            closeBtn.onclick = () => {
                modal.classList.remove('show');
                resolve();
            };
            // 모달 바깥 클릭 시 닫기
            modal.onclick = (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                    resolve();
                }
            };
        });
    },

    formatPhoneNumber(value) {
        if (!value) return value;
        const phoneNumber = value.replace(/[^\d]/g, '');
        const phoneNumberLength = phoneNumber.length;
        if (phoneNumberLength < 4) return phoneNumber;
        if (phoneNumberLength < 8) {
            return `${phoneNumber.slice(0, 3)}-${phoneNumber.slice(3)}`;
        }
        return `${phoneNumber.slice(0, 3)}-${phoneNumber.slice(3, 7)}-${phoneNumber.slice(7, 11)}`;
    },

    handlePhoneInput(e) {
        const formattedValue = this.formatPhoneNumber(e.target.value);
        e.target.value = formattedValue;
    },

    // 우리 API 값(M/F, develop/medical/research, pending/staff/admin)을 화면 표시용 한글로 바꿈
    genderLabel(value) {
        return { M: '남성', F: '여성' }[value] || value;
    },

    departmentLabel(value) {
        return { develop: '개발팀', medical: '의료진', research: '연구진' }[value] || value;
    },

    roleLabel(value) {
        return { pending: '승인대기', staff: '일반회원', admin: '관리자' }[value] || value;
    },

    templatesCache: {},

    async loadTemplate(name) {
        if (this.templatesCache[name]) return this.templatesCache[name];
        const response = await fetch(`/static/templates/${name}.html`);
        const html = await response.text();
        this.templatesCache[name] = html;
        return html;
    }
};
