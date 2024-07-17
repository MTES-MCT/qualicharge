# -- Custom image --
FROM quay.io/jupyter/base-notebook:notebook-7.2.1

# Install base dependencies
#
# FIXME: jupytext 1.16.4+ seems to fix the issue but is not released yet
#        see: https://github.com/mwouts/jupytext/issues/1260
RUN mamba install --yes \
      duckdb \
      geopandas \
      jupytext==1.16.2 \
      matplotlib \
      pandas \
      psycopg[binary,pool] \
      seaborn
