class Pagination {
    constructor({
        totalPagesSelector,
        goToPageButtonId,
        pageInputId,
        pageLinkId,
        tableId = 'leads-table' // По умолчанию 'leads-table', но можно изменить
    }) {
        this.totalPagesSelector = totalPagesSelector;
        this.goToPageButtonId = goToPageButtonId;
        this.pageInputId = pageInputId;
        this.pageLinkId = pageLinkId;
        this.tableId = tableId;

        this.init();
    }

    init() {
        document.addEventListener("DOMContentLoaded", () => {
            const totalPages = parseInt(document.querySelector(this.totalPagesSelector)?.value, 10);
            if (totalPages) {
                this.initializePaginationLogic(totalPages);
            }
        });

        document.body.addEventListener('htmx:afterSwap', (event) => {
            const table = document.getElementById(this.tableId);
            if (table) {
                const totalPages = parseInt(document.querySelector(this.totalPagesSelector)?.value, 10);
                if (totalPages) {
                    this.initializePaginationLogic(totalPages);
                }
            }
        });
    }

    initializePaginationLogic(totalPages) {
        const goToPageButton = document.getElementById(this.goToPageButtonId);
        const pageInput = document.getElementById(this.pageInputId);

        if (goToPageButton && pageInput) {
            goToPageButton.removeEventListener('click', this.handleGoToPageClick);
            goToPageButton.addEventListener('click', () => this.handleGoToPageClick(totalPages));
        }

        const pageLinks = document.querySelectorAll(this.pageLinkId);
        if (pageLinks.length > 0) {
            pageLinks.forEach(link => {
                link.removeEventListener('click', this.handlePageLinkClick);
                link.addEventListener('click', this.handlePageLinkClick);
            });
        }
    }

    handleGoToPageClick(totalPages) {
        const pageInput = document.getElementById(this.pageInputId);
        const pageNumber = parseInt(pageInput.value, 10);
        if (isNaN(pageNumber)) {
            alert("Введите корректный номер страницы.");
            return;
        }
        if (pageNumber >= 1 && pageNumber <= totalPages) {
            let urlParams = new URLSearchParams(window.location.search);
            urlParams.set('page', pageNumber);
            window.location.search = urlParams.toString();
        } else {
            alert(`Введите номер страницы от 1 до ${totalPages}`);
        }
    }

    handlePageLinkClick(event) {
        event.preventDefault();
        const pageNumber = new URL(this.href).searchParams.get('page');
        if (pageNumber) {
            window.location.href = this.href;
        }
    }
}