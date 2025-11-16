function searchTable() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let table = document.getElementById("tasksTable");
    let trs = table.getElementsByTagName("tr");
    for (let i=1; i<trs.length; i++){
        let tds = trs[i].getElementsByTagName("td");
        let show=false;
        // check available cells (title at 1, assignee at 2) safely
        for(let j=1;j<=2 && j<tds.length;j++){ // title and assignee
            let text = (tds[j].innerText || '').toLowerCase();
            if(text.indexOf(input) > -1) show=true;
        }
        trs[i].style.display = show ? "" : "none";
    }
}

function deleteTask(id, title){
    // normalize id and title
    if (typeof id === 'string') id = id.trim();
    title = title || '';
    if(confirm(`Удалить задачу "${title}"?`)){
        fetch(`/task/${id}/delete`, {method:'POST'})
        .then(res=>res.json())
        .then(data=>{
            if(data.success) location.reload();
        }).catch(err=>{
            console.error('Delete failed', err);
            alert('Не удалось удалить задачу.');
        });
    }
}

// Attach event listener for dynamically added delete buttons
document.addEventListener('DOMContentLoaded', function(){
    document.body.addEventListener('click', function(e){
        const btn = e.target.closest && e.target.closest('.delete-btn');
        if(!btn) return;
        const id = btn.dataset.id;
        const title = btn.dataset.title;
        deleteTask(id, title);
    });
    // set min date for any due_date inputs
    const due = document.getElementById('due_date');
    if(due && due.type === 'date'){
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth()+1).padStart(2,'0');
        const dd = String(today.getDate()).padStart(2,'0');
        due.min = `${yyyy}-${mm}-${dd}`;
        if(!due.value) due.value = `${yyyy}-${mm}-${dd}`;
    }

    // make tables sortable: attach click handlers to th with data-type
    document.querySelectorAll('table#tasksTable').forEach(table=>{
        const ths = table.querySelectorAll('thead th');
        ths.forEach((th, idx)=>{
            const type = th.dataset.type || 'string';
            th.style.cursor = 'pointer';
            th.addEventListener('click', ()=>{
                const currentlyAsc = th.classList.contains('sort-asc');
                // remove classes from all headers
                ths.forEach(h=>h.classList.remove('sort-asc','sort-desc'));
                th.classList.add(currentlyAsc ? 'sort-desc' : 'sort-asc');
                sortTableByColumn(table, idx, !currentlyAsc, type);
            });
        });
    });
});

function sortTableByColumn(table, column, asc=true, type='string'){
    const tbody = table.tBodies[0];
    if(!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const collator = new Intl.Collator('ru', {numeric:true, sensitivity:'base'});
    rows.sort((a,b)=>{
        let aText = (a.cells[column] && a.cells[column].innerText) ? a.cells[column].innerText.trim() : '';
        let bText = (b.cells[column] && b.cells[column].innerText) ? b.cells[column].innerText.trim() : '';
        if(type === 'number'){
            const an = parseFloat(aText.replace(/[^0-9.-]+/g,'')) || 0;
            const bn = parseFloat(bText.replace(/[^0-9.-]+/g,'')) || 0;
            return asc ? an - bn : bn - an;
        }
        if(type === 'date'){
            const ad = aText ? Date.parse(aText) : 0;
            const bd = bText ? Date.parse(bText) : 0;
            return asc ? ad - bd : bd - ad;
        }
        // default: string
        return asc ? collator.compare(aText, bText) : collator.compare(bText, aText);
    });
    // append in new order
    rows.forEach(r=>tbody.appendChild(r));
}
