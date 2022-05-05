/*
 * Contains utility functions.
 */

// Returns [0 ... len]
export function range(len: number): number[] {
	return [...Array(len).keys()];
}
// Returns sum of array values
export function arraySum(array: number[]): number {
	return array.reduce((x,y) => x+y);
}
// Returns an array of increasing evenly-spaced numbers from 'start' to 'end' with size 'size'
export function linspace(start: number, end: number, size: number): number[] {
	let step = (end - start) / (size - 1);
	let ar = [];
	for (let i = 0; i < size; i++){
		ar.push(start + step * i);
	}
	return ar;
}
// Returns array copy with vals clipped to within [min,max], redistributing to compensate
// Returns null on failure
export function limitVals(arr: number[], min: number, max: number): number[] | null {
	let vals = [...arr];
	let clipped = new Array(vals.length).fill(false);
	let owedChg = 0; // Stores total change made after clipping values
	while (true){
		// Clip values
		for (let i = 0; i < vals.length; i++){
			if (clipped[i]){
				continue;
			}
			if (vals[i] < min){
				owedChg += vals[i] - min;
				vals[i] = min;
				clipped[i] = true;
			} else if (vals[i] > max){
				owedChg += vals[i] - max;
				vals[i] = max;
				clipped[i] = true;
			}
		}
		if (Math.abs(owedChg) < Number.EPSILON){
			return vals;
		}
		// Compensate for changes made
		let indicesToUpdate = (owedChg > 0) ?
			range(vals.length).filter(idx => vals[idx] < max) :
			range(vals.length).filter(idx => vals[idx] > min);
		if (indicesToUpdate.length == 0){
			return null;
		}
		for (let i of indicesToUpdate){
			vals[i] += owedChg / indicesToUpdate.length;
		}
		owedChg = 0;
	}
}
// Usable to iterate through possible int arrays with ascending values in the range 0 to maxLen-1, starting with [0]
	// eg: With maxLen 3, updates [0] to [0,1], then to [0,2], then [0,1,2]
// Returns false when there is no next array
export function updateAscSeq(seq: number[], maxLen: number): boolean {
	// Try increasing last element, then preceding elements, then extending the array
	let i = seq.length - 1;
	while (true){
		if (i > 0 && seq[i] < (maxLen - 1) - (seq.length - 1 - i)){
			seq[i]++;
			return true;
		} else if (i > 0){
			i--;
		} else {
			if (seq.length < maxLen){
				seq.push(0);
				seq.splice(0, seq.length, ...range(seq.length));
				return true;
			} else {
				return false;
			}
		}
	}
}
// Given a non-empty array of non-negative weights, returns an array index chosen with weighted pseudorandomness
// Returns null if array contains all zeros
export function randWeightedChoice(weights: number[]): number | null {
	let thresholds = Array(weights.length);
	let sum = 0;
	for (let i = 0; i < weights.length; i++){
		sum += weights[i];
		thresholds[i] = sum;
	}
	let rand = Math.random();
	for (let i = 0; i < weights.length; i++){
		if (rand <= thresholds[i] / sum){
			return i;
		}
	}
	return null;
}
// Returns a string with words first-letter capitalised
export function capitalizeWords(str: string){
	return str.replace(/\b\w/g, x => x.toUpperCase());
		// '\b' matches word boundary, '\w' is like [a-zA-Z0-9_],
}
