# DAGdown

short hand notation to define yadage workflows. DAGdown is to yadage workflows as Markdown to HTML.


    cat test.dd | python dagdown.py > workflow.yml
    yadage-run work workflow.yml -p nevents=100

or 

    yadage-run work dagdown:test.dd -p nevents=100 --visualize --plugins dagdown
