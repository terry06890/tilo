export {defaultLayout, initTree};

const DEFAULT_TILE_SPACING = 5;
const DEFAULT_HEADER_SZ = 20;

const staticSqrLayout = { //determines layout for squares in a specified rectangle, with spacing
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h){
		//get number-of-columns with highest occupied-fraction of rectangles with aspect-ratio w/h
			//account for tile-spacing?, account for parent-box-border?,
		let numTiles = nodes.length, ar = w/h;
		let numCols, numRows, bestFrac = 0;
		for (let nc = 1; nc <= numTiles; nc++){
			let nr = Math.ceil(numTiles/nc);
			let ar2 = nc/nr;
			let frac = ar > ar2 ? ar2/ar : ar/ar2;
			if (frac > bestFrac){
				bestFrac = frac;
				numCols = nc;
				numRows = nr;
			}
		}
		//compute other parameters
		let tileSz = Math.min(
			((w - this.TILE_SPACING) / numCols) - this.TILE_SPACING,
			((h - this.TILE_SPACING) / numRows) - this.TILE_SPACING);
		//determine layout
		return Object.fromEntries(
			nodes.map((el, idx) => [el.tolNode.name, {
				x: x0 + (idx % numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
				y: y0 + Math.floor(idx / numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
				w: tileSz,
				h: tileSz
				}])
			);
	},
	initLayoutInfo(tree){
		return;
	},
	updateLayoutInfoOnExpand(nodeList){
		return;
	},
	updateLayoutInfoOnCollapse(nodeList){
		return;
	}
};
const staticRectLayout = {
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h){
		//get number-of-columns with highest tileCount-proportions-alignment
		let numTiles = nodes.length;
		let tileCounts = nodes.map(e => e.tileCount);
		let tileCountTotal = tileCounts.reduce((x, y) => x+y);
		let numCols, bestScore = Number.NEGATIVE_INFINITY, rowProportions, colProportions;
		for (let nc = 1; nc <= numTiles; nc++){
			let nr = Math.ceil(numTiles/nc);
			//create grid representing each tile's tileCount (0 for no tile)
			let grid = Array(nr).fill().map(e => Array(nc).fill(0));
			for (let i = 0; i < tileCounts.length; i++){
				grid[Math.floor(i / nc)][i % nc] = tileCounts[i];
			}
			//get totals across each row/column divided by tileCountTotal
			let rowProp = grid.map(e => e.reduce((x, y) => x+y) / tileCountTotal);
			let colProp = [...Array(nc).keys()].map(c =>
				[...Array(nr).keys()].map(r => grid[r][c]).reduce((x,y) => x+y) / tileCountTotal);
			//get score
			let score = 0;
			for (let r = 0; r < nr; r++){
				for (let c = 0; c < nc; c++){
					if (grid[r][c] > 0){
						score -= Math.abs(grid[r][c] - (rowProp[r] * colProp[c]));
					}
				}
			}
			//also score for w/h occupation?
			if (score > bestScore){
				bestScore = score;
				numCols = nc;
				rowProportions = rowProp;
				colProportions = colProp;
			}
		}
		//determine layout
		let rowNetProps = [0];
		for (let i = 0; i < rowProportions.length-1; i++){
			rowNetProps.push(rowNetProps[i] + rowProportions[i]);
		}
		let colNetProps = [0];
		for (let i = 0; i < colProportions.length-1; i++){
			colNetProps.push(colNetProps[i] + colProportions[i]);
		}
		let retVal = Object.fromEntries(
			nodes.map((el, idx) => [el.tolNode.name, {
				x: x0 + colNetProps[idx % numCols]*(w - this.TILE_SPACING) + this.TILE_SPACING,
				y: y0 + rowNetProps[Math.floor(idx / numCols)]*(h - this.TILE_SPACING) + this.TILE_SPACING,
				w: colProportions[idx % numCols]*(w - this.TILE_SPACING) - this.TILE_SPACING,
				h: rowProportions[Math.floor(idx / numCols)]*(h - this.TILE_SPACING) - this.TILE_SPACING
				}]));
		return retVal;
	},
	initLayoutInfo(tree){ //initialise node-tree with tile-counts
		if (tree.children.length == 0){
			tree.tileCount = 1;
		} else {
			tree.children.forEach(e => this.initLayoutInfo(e));
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
		}
	},
	updateLayoutInfoOnExpand(nodeList){ //given list of tree-nodes from expanded_child-to-parent, update tile-counts
		nodeList[0].children.forEach(e => {e.tileCount = 1});
		nodeList[0].tileCount = nodeList[0].children.length;
		for (let i = 1; i < nodeList.length; i++){
			nodeList[i].tileCount += nodeList[0].tileCount - 1;
		}
	},
	updateLayoutInfoOnCollapse(nodeList){ //given list of tree-nodes from child_to_collapse-to-parent, update tile-counts
		let tc = nodeList[0].tileCount;
		nodeList[0].tileCount = 1;
		for (let i = 1; i < nodeList.length; i++){
			nodeList[i].tileCount -= tc - 1;
		}
	}
};
const sweepToSideLayout = {
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h){
		//separate leaf and non-leaf nodes
		let leaves = [], nonLeaves = [];
		nodes.forEach(e => (e.children.length == 0 ? leaves : nonLeaves).push(e));
		//determine layout
		if (nonLeaves.length == 0){ //if all leaves, use squares-layout
			return staticSqrLayout.genLayout(nodes, x0, y0, w, h);
		} else { //if some non-leaves, use rect-layout
			let retVal = {};
			if (leaves.length > 0){
				let ratio = leaves.length / (leaves.length + nonLeaves.map(e => e.tileCount).reduce((x,y) => x+y));
				retVal = staticSqrLayout.genLayout(leaves, x0, y0, w*ratio, h);
				x0 += w*ratio - this.TILE_SPACING;
				w -= (w*ratio - this.TILE_SPACING);
			}
			//return {...retVal, ...staticSqrLayout.genLayout(nonLeaves, x0, y0, w, h)};
			return {...retVal, ...staticRectLayout.genLayout(nonLeaves, x0, y0, w, h)};
		}
	},
	initLayoutInfo(tree){
		staticRectLayout.initLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList){
		staticRectLayout.updateLayoutInfoOnExpand(nodeList);
	},
	updateLayoutInfoOnCollapse(nodeList){
		staticRectLayout.updateLayoutInfoOnCollapse(nodeList);
	}
};
let defaultLayout = sweepToSideLayout;

function initTree(tol, lvl, layout = defaultLayout){
	let tree = {tolNode: tol, children: []};
	initTreeRec(tree, lvl);
	layout.initLayoutInfo(tree)
	return tree;
}
function initTreeRec(tree, lvl){
	if (lvl > 0){
		tree.children = tree.tolNode.children.map(e => initTreeRec({tolNode: e, children: []}, lvl-1));
	}
	return tree;
}
