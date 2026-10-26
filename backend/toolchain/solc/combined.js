const solc = require('solc');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const files = args.filter((a) => a.endsWith('.sol'));
const sources = {};
for (const f of files) sources[f] = { content: fs.readFileSync(f, 'utf8') };

const input = {
  language: 'Solidity',
  sources,
  settings: {
    outputSelection: {
      '*': {
        '': ['ast'],
        '*': ['abi', 'evm.bytecode', 'evm.deployedBytecode', 'evm.methodIdentifiers', 'userdoc', 'devdoc'],
      },
    },
  },
};

const findImports = (p) => {
  try {
    return { contents: fs.readFileSync(path.resolve(p), 'utf8') };
  } catch {
    return { error: 'not found' };
  }
};

const out = JSON.parse(solc.compile(JSON.stringify(input), { import: findImports }));
const fatal = (out.errors || []).filter((e) => e.severity === 'error');
if (fatal.length) {
  process.stderr.write(fatal.map((e) => e.formattedMessage).join('\n'));
  process.exit(1);
}

const contracts = {};
for (const [file, byName] of Object.entries(out.contracts || {})) {
  for (const [name, c] of Object.entries(byName)) {
    contracts[`${file}:${name}`] = {
      abi: c.abi,
      bin: c.evm.bytecode.object,
      'bin-runtime': c.evm.deployedBytecode.object,
      srcmap: c.evm.bytecode.sourceMap,
      'srcmap-runtime': c.evm.deployedBytecode.sourceMap,
      userdoc: c.userdoc,
      devdoc: c.devdoc,
      hashes: c.evm.methodIdentifiers,
    };
  }
}

const sourceList = Object.keys(out.sources).sort((a, b) => out.sources[a].id - out.sources[b].id);
const astSources = {};
for (const f of sourceList) astSources[f] = { AST: out.sources[f].ast };

process.stdout.write(JSON.stringify({ contracts, sourceList, sources: astSources, version: solc.version() }));
