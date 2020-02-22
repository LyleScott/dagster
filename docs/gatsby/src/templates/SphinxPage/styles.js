export const wrapper = {
  display: "flex",
  height: "100%"
};

export const content = {
  flex: 1,
  py: [3, 4, 5],
  px: [3, 4, 5],
  maxWidth: ["100%", "100%", "calc(100% - 280px)"]
};

export const icon = {
  mr: 1
};

export const btnShowToc = {
  my: 3,
  py: 1,
  px: 2,
  borderRadius: "radius",
  appearance: "none",
  border: t => `1px solid ${t.colors.lightGray[1]}`,
  bg: "lightGray.3",
  display: "flex",
  alignItems: "center",
  textTransform: "uppercase",
  fontSize: 12,
  fontWeight: "bold",
  color: "gray.1"
};

export const pageLinks = {
  display: "flex",
  justifyContent: "space-between",
  pt: [2, 3, 3],
  mt: [2, 3, 3],
  borderTop: t => `1px solid ${t.colors.lightGray[1]}`,

  a: {
    display: "inline-flex",
    alignItems: "center"
  },

  svg: {
    stroke: "gray.1"
  },

  "svg.left": {
    mr: 2
  },
  "svg.right": {
    ml: 2
  }
};
