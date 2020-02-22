export const wrapper = {
  m: 0,

  "&.active.toctree-l1": {
    mb: 2,
    fontSize: 2
  },
  "&:not(.active) > ul": {
    display: "none"
  },
  "&.toctree-l2": {
    lineHeight: 1.3,
    whiteSpace: "normal"
  },
  "&.toctree-l2 a": {
    fontSize: 1,
    opacity: 0.6
  },
  "&.toctree-l2 a:hover, &.toctree-l2 a.active": {
    opacity: 1
  },
  "&.toctree-l2 > ul": {
    display: "none"
  }
};
