#!/usr/bin/env bash
# language=sh
# set -euo pipefail
set -x # echo commands

IMAGE=andreacensi/mcdp_books@sha256:307d478c8cedaff574e4a94303dae779547a513bd0641e3d4c236a5206b6c77b


short=$1
src=$2

echo src = ${src}
echo short = ${short}


if [ "$CI" = "" ]
then
   branch=`git -C ${src} rev-parse --abbrev-ref HEAD`
else
   branch=${CIRCLE_BRANCH}
fi

#toplevel=`git -C ${src} rev-parse --show-toplevel`
#repo=`basename ${toplevel}`

org=`git config --get remote.origin.url | cut -f2 -d":"  | cut -f1 -d/ | tr '[:upper:]' '[:lower:]'`

repo=duckuments
base=https://docs-branches.duckietown.org/${org}/${repo}/branch/${branch}
permalink_prefix=${base}/${short}/out

#cross=${base}/all_crossref.html


if [ "$CI" = "" ]
then
   echo "Not on Circle, using parallel compilation."
   cmd="rparmake n=4"
   #extra_crossrefs=${base}/all_crossref.html
   #options1="--extra_crossrefs ${extra_crossrefs}"
   options1=""
else
   echo "On Circle, not using parallel compilation to avoid running out of memory."
   cmd=rmake
   options1=""
fi


dist=duckuments-dist

if [ "$ONLY_FOR_REFS" = "" ]
then
   options2="--output_file ${dist}/${short}/out.html --split ${dist}/${short}/out/ --resolve_external"

else
   echo "Skipping polish, ONLY_FOR_REFS"

   # XXX: need to do split because of cross refs
   options2="--split ${dist}/${short}/out/ --ignore_ref_errors --only_refs"
fi

# only andrea and CI build the PDF version

if [ "$USER" = "andrea" ]
then
    options2="${options2} --pdf ${dist}/${short}/out.pdf"
fi

if [ "$CI" = "" ]
then
   echo
else
   options2="${options2} --pdf ${dist}/${short}/out.pdf"
fi


mkdir -p ${dist}





echo IMAGE: ${IMAGE}

tmpdir=/my-tmp

mkdir -p /tmp/${USER}

gitdir_super=`git -C ${src} rev-parse --show-superproject-working-tree`
gitdir=`git -C ${src}  rev-parse --show-toplevel`

docker_run="docker run
-it
-v ${gitdir}:${gitdir}
-v ${gitdir_super}:${gitdir_super}
-v ${PWD}:${PWD}
-v /tmp/${USER}:/home/${USER}
-e USER=${USER}
-e USERID=${UID}
--user $UID
-w ${PWD}
${IMAGE}"


resources="docs/resources/common:docs/resources/templates/duckiebook1:${dist}"


#--likebtn 5ae54e0d6fd08bb24f3a7fa1 \

${docker_run} mcdp-render-manual \
    --src "${src}" \
    --bookshort "${short}" \
    --resources "${resources}" \
    --stylesheet v_manual_split \
    --stylesheet_pdf v_manual_blurb_ready \
    --wordpress_integration \
    --output_crossref "${dist}/${short}/crossref.html" \
    -o "out/${short}" \
    --permalink_prefix ${permalink_prefix} \
    ${options1} \
    ${options2} \
    -c "config echo 1; ${cmd}"


${docker_run} python -m mcdp_docs.make_index docs/resources/books.yaml \
    ${dist}/index.html \
    ${dist}/all_crossref.html \
    ${dist}/errors_and_warnings.pickle
