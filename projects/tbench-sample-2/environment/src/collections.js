function getOrCreate(map, key, create) {
  if (!map.has(key)) map.set(key, create());
  return map.get(key);
}

module.exports = { getOrCreate };
