const R = require("ramda");

const pageQuery = `{
  pages: allSphinxPage(limit: 10000) {
    edges {
      node {
        objectID: id,
        title
        markdown
        slug
      }
    }
  }
}`;

const settings = {
  attributesToSnippet: [`markdown:20`]
};

const recordChunker = (accumulator, currentValue) => {
  if (currentValue.markdown.length <= 10000) {
    accumulator.push(currentValue);
    return accumulator;
  } else {
    var markdown = currentValue.markdown;
    const objectID = currentValue.objectID;
    var i = 0;
    while (markdown.length > 0) {
      var nextValue = {
        objectID: currentValue.objectID,
        title: currentValue.title,
        markdown: currentValue.markdown,
        slug: currentValue.slug
      };
      nextValue.markdown = markdown.slice(0, 10000);
      nextValue.objectID = objectID + "_" + i.toString();
      i = i + 1;
      accumulator.push(nextValue);
      markdown = markdown.slice(10000);
    }
    return accumulator;
  }
};

const queries = [
  {
    settings,
    query: pageQuery,
    indexName: `Pages`,
    transformer: ({ data }) => {
      return data.pages.edges
        .filter(({ node }) => node.slug && !node.slug.startsWith("_modules"))
        .map(R.prop("node"))
        .reduce(recordChunker, []);
    }
  },
  {
    settings: {
      attributesToSnippet: [`markdown:20`],
      queryLanguages: ["en"],
      distinct: true,
      attributeForDistinct: "title"
    },
    query: pageQuery,
    indexName: `Modules`,
    transformer: ({ data }) => {
      return data.pages.edges
        .filter(({ node }) => node.slug && node.slug.startsWith("_modules"))
        .map(R.prop("node"))
        .reduce(recordChunker, []);
    }
  }
];

module.exports = queries;
