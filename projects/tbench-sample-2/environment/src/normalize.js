function normalizeEmail(email) {
  if (typeof email !== 'string') return '';
  return email.toLowerCase();
}

function normalizeListId(listId) {
  if (typeof listId !== 'string') return '';
  return listId;
}

module.exports = { normalizeEmail, normalizeListId };
