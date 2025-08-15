"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/typed-array-buffer";
exports.ids = ["vendor-chunks/typed-array-buffer"];
exports.modules = {

/***/ "(ssr)/./node_modules/typed-array-buffer/index.js":
/*!**************************************************!*\
  !*** ./node_modules/typed-array-buffer/index.js ***!
  \**************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval("\nvar $TypeError = __webpack_require__(/*! es-errors/type */ \"(ssr)/./node_modules/es-errors/type.js\");\nvar callBound = __webpack_require__(/*! call-bound */ \"(ssr)/./node_modules/call-bound/index.js\");\n/** @type {undefined | ((thisArg: import('.').TypedArray) => Buffer<ArrayBufferLike>)} */ var $typedArrayBuffer = callBound(\"TypedArray.prototype.buffer\", true);\nvar isTypedArray = __webpack_require__(/*! is-typed-array */ \"(ssr)/./node_modules/is-typed-array/index.js\");\n/** @type {import('.')} */ // node <= 0.10, < 0.11.4 has a nonconfigurable own property instead of a prototype getter\nmodule.exports = $typedArrayBuffer || function typedArrayBuffer(x) {\n    if (!isTypedArray(x)) {\n        throw new $TypeError(\"Not a Typed Array\");\n    }\n    return x.buffer;\n};\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvdHlwZWQtYXJyYXktYnVmZmVyL2luZGV4LmpzIiwibWFwcGluZ3MiOiJBQUFBO0FBRUEsSUFBSUEsYUFBYUMsbUJBQU9BLENBQUM7QUFFekIsSUFBSUMsWUFBWUQsbUJBQU9BLENBQUM7QUFFeEIsdUZBQXVGLEdBQ3ZGLElBQUlFLG9CQUFvQkQsVUFBVSwrQkFBK0I7QUFFakUsSUFBSUUsZUFBZUgsbUJBQU9BLENBQUM7QUFFM0Isd0JBQXdCLEdBQ3hCLDBGQUEwRjtBQUMxRkksT0FBT0MsT0FBTyxHQUFHSCxxQkFBcUIsU0FBU0ksaUJBQWlCQyxDQUFDO0lBQ2hFLElBQUksQ0FBQ0osYUFBYUksSUFBSTtRQUNyQixNQUFNLElBQUlSLFdBQVc7SUFDdEI7SUFDQSxPQUFPUSxFQUFFQyxNQUFNO0FBQ2hCIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vdHJhZGVzZWVyLW1pbmlhcHAvLi9ub2RlX21vZHVsZXMvdHlwZWQtYXJyYXktYnVmZmVyL2luZGV4LmpzPzllOWEiXSwic291cmNlc0NvbnRlbnQiOlsiJ3VzZSBzdHJpY3QnO1xuXG52YXIgJFR5cGVFcnJvciA9IHJlcXVpcmUoJ2VzLWVycm9ycy90eXBlJyk7XG5cbnZhciBjYWxsQm91bmQgPSByZXF1aXJlKCdjYWxsLWJvdW5kJyk7XG5cbi8qKiBAdHlwZSB7dW5kZWZpbmVkIHwgKCh0aGlzQXJnOiBpbXBvcnQoJy4nKS5UeXBlZEFycmF5KSA9PiBCdWZmZXI8QXJyYXlCdWZmZXJMaWtlPil9ICovXG52YXIgJHR5cGVkQXJyYXlCdWZmZXIgPSBjYWxsQm91bmQoJ1R5cGVkQXJyYXkucHJvdG90eXBlLmJ1ZmZlcicsIHRydWUpO1xuXG52YXIgaXNUeXBlZEFycmF5ID0gcmVxdWlyZSgnaXMtdHlwZWQtYXJyYXknKTtcblxuLyoqIEB0eXBlIHtpbXBvcnQoJy4nKX0gKi9cbi8vIG5vZGUgPD0gMC4xMCwgPCAwLjExLjQgaGFzIGEgbm9uY29uZmlndXJhYmxlIG93biBwcm9wZXJ0eSBpbnN0ZWFkIG9mIGEgcHJvdG90eXBlIGdldHRlclxubW9kdWxlLmV4cG9ydHMgPSAkdHlwZWRBcnJheUJ1ZmZlciB8fCBmdW5jdGlvbiB0eXBlZEFycmF5QnVmZmVyKHgpIHtcblx0aWYgKCFpc1R5cGVkQXJyYXkoeCkpIHtcblx0XHR0aHJvdyBuZXcgJFR5cGVFcnJvcignTm90IGEgVHlwZWQgQXJyYXknKTtcblx0fVxuXHRyZXR1cm4geC5idWZmZXI7XG59O1xuIl0sIm5hbWVzIjpbIiRUeXBlRXJyb3IiLCJyZXF1aXJlIiwiY2FsbEJvdW5kIiwiJHR5cGVkQXJyYXlCdWZmZXIiLCJpc1R5cGVkQXJyYXkiLCJtb2R1bGUiLCJleHBvcnRzIiwidHlwZWRBcnJheUJ1ZmZlciIsIngiLCJidWZmZXIiXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/typed-array-buffer/index.js\n");

/***/ })

};
;