// Toggle template help content
function toggleTemplateHelp() {
    const helpContent = document.getElementById('template-help-content');
    if (helpContent) {
        if (helpContent.style.display === 'none') {
            helpContent.style.display = 'block';
        } else {
            helpContent.style.display = 'none';
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Notification template help initialized');
});
