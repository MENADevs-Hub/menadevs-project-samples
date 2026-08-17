function normalizeEmail(email) {
  if (typeof email !== 'string') return '';
  return email.trim().toLowerCase();
}

function normalizeListId(listId) {
  if (typeof listId !== 'string') return '';
  return listId.trim();
}

module.exports = { normalizeEmail, normalizeListId };
