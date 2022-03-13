export class TolNode {
	name: string;
	children: TolNode[];
	constructor(name: string, children: TolNode[] = []){
		this.name = name;
		this.children = children;
	}
}
export class LayoutNode {
	//set by TileTree and LayoutFn funcs, eventually used by Tile
	tolNode: TolNode;
	children: LayoutNode[];
	pos: [number, number];
	dims: [number, number];
	headerSz: number;
	//set by layoutInfoHooks, used by LayoutFn funcs
	tileCount: number;
	//set_by/internal_to LayoutFn funcs
	usedDims: [number, number];
	empSpc: number;
	//set by LayoutFn funcs, eventually used by Tile
	sepSweptArea: SepSweptArea | null;
	//
	constructor(
		tolNode: TolNode, children: LayoutNode[], pos:[number,number]=[0,0], dims:[number,number]=[0,0],
		{headerSz=0, tileCount=0, usedDims=[0,0] as [number,number],
			empSpc=0, sepSweptArea=null as SepSweptArea|null} = {}){
		this.tolNode = tolNode;
		this.children = children;
		this.pos = pos;
		this.dims = dims;
		this.headerSz = headerSz;
		this.tileCount = tileCount;
		this.usedDims = usedDims;
		this.empSpc = empSpc;
		this.sepSweptArea = sepSweptArea;
	}
}
export class SepSweptArea {
	pos: [number, number];
	dims: [number, number];
	sweptLeft: boolean;
	tileSpacing: number;
	constructor(pos: [number, number], dims: [number, number], sweptLeft: boolean, tileSpacing: number){
		this.pos = pos;
		this.dims = dims;
		this.sweptLeft = sweptLeft;
		this.tileSpacing = tileSpacing;
	}
}
