const { run } = require("../src/index");
if (typeof run !== "function") {
  throw new Error("run export missing");
}
console.log("ok");
