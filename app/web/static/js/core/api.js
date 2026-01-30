// Api para la pagina de dashboard y POS de ventas
window.api = (path, opts={}) =>
  fetch(path, { headers: {"Content-Type":"application/json"}, ...opts });