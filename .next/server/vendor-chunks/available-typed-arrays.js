"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/available-typed-arrays";
exports.ids = ["vendor-chunks/available-typed-arrays"];
exports.modules = {

/***/ "(ssr)/./node_modules/available-typed-arrays/index.js":
/*!******************************************************!*\
  !*** ./node_modules/available-typed-arrays/index.js ***!
  \******************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval("\nvar possibleNames = __webpack_require__(/*! possible-typed-array-names */ \"(ssr)/./node_modules/possible-typed-array-names/index.js\");\nvar g = typeof globalThis === \"undefined\" ? global : globalThis;\n/** @type {import('.')} */ module.exports = function availableTypedArrays() {\n    var /** @type {ReturnType<typeof availableTypedArrays>} */ out = [];\n    for(var i = 0; i < possibleNames.length; i++){\n        if (typeof g[possibleNames[i]] === \"function\") {\n            // @ts-expect-error\n            out[out.length] = possibleNames[i];\n        }\n    }\n    return out;\n};\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvYXZhaWxhYmxlLXR5cGVkLWFycmF5cy9pbmRleC5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUVBLElBQUlBLGdCQUFnQkMsbUJBQU9BLENBQUM7QUFFNUIsSUFBSUMsSUFBSSxPQUFPQyxlQUFlLGNBQWNDLFNBQVNEO0FBRXJELHdCQUF3QixHQUN4QkUsT0FBT0MsT0FBTyxHQUFHLFNBQVNDO0lBQ3pCLElBQUksb0RBQW9ELEdBQUdDLE1BQU0sRUFBRTtJQUNuRSxJQUFLLElBQUlDLElBQUksR0FBR0EsSUFBSVQsY0FBY1UsTUFBTSxFQUFFRCxJQUFLO1FBQzlDLElBQUksT0FBT1AsQ0FBQyxDQUFDRixhQUFhLENBQUNTLEVBQUUsQ0FBQyxLQUFLLFlBQVk7WUFDOUMsbUJBQW1CO1lBQ25CRCxHQUFHLENBQUNBLElBQUlFLE1BQU0sQ0FBQyxHQUFHVixhQUFhLENBQUNTLEVBQUU7UUFDbkM7SUFDRDtJQUNBLE9BQU9EO0FBQ1IiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly90cmFkZXNlZXItbWluaWFwcC8uL25vZGVfbW9kdWxlcy9hdmFpbGFibGUtdHlwZWQtYXJyYXlzL2luZGV4LmpzPzE3NWYiXSwic291cmNlc0NvbnRlbnQiOlsiJ3VzZSBzdHJpY3QnO1xuXG52YXIgcG9zc2libGVOYW1lcyA9IHJlcXVpcmUoJ3Bvc3NpYmxlLXR5cGVkLWFycmF5LW5hbWVzJyk7XG5cbnZhciBnID0gdHlwZW9mIGdsb2JhbFRoaXMgPT09ICd1bmRlZmluZWQnID8gZ2xvYmFsIDogZ2xvYmFsVGhpcztcblxuLyoqIEB0eXBlIHtpbXBvcnQoJy4nKX0gKi9cbm1vZHVsZS5leHBvcnRzID0gZnVuY3Rpb24gYXZhaWxhYmxlVHlwZWRBcnJheXMoKSB7XG5cdHZhciAvKiogQHR5cGUge1JldHVyblR5cGU8dHlwZW9mIGF2YWlsYWJsZVR5cGVkQXJyYXlzPn0gKi8gb3V0ID0gW107XG5cdGZvciAodmFyIGkgPSAwOyBpIDwgcG9zc2libGVOYW1lcy5sZW5ndGg7IGkrKykge1xuXHRcdGlmICh0eXBlb2YgZ1twb3NzaWJsZU5hbWVzW2ldXSA9PT0gJ2Z1bmN0aW9uJykge1xuXHRcdFx0Ly8gQHRzLWV4cGVjdC1lcnJvclxuXHRcdFx0b3V0W291dC5sZW5ndGhdID0gcG9zc2libGVOYW1lc1tpXTtcblx0XHR9XG5cdH1cblx0cmV0dXJuIG91dDtcbn07XG4iXSwibmFtZXMiOlsicG9zc2libGVOYW1lcyIsInJlcXVpcmUiLCJnIiwiZ2xvYmFsVGhpcyIsImdsb2JhbCIsIm1vZHVsZSIsImV4cG9ydHMiLCJhdmFpbGFibGVUeXBlZEFycmF5cyIsIm91dCIsImkiLCJsZW5ndGgiXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/available-typed-arrays/index.js\n");

/***/ })

};
;