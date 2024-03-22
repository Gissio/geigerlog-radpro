// js for gauge version 2

// keep for reference:
// <style>
// /* .gauge  {text-align:right; padding-left:0px;} */
// /* .gauge-container{font-family:Helvetica,Arial,sans-serif;text-align:right;} */
// /* .gauge g.arc{fill:steelblue;} */
// /* .gauge g.pointer{fill:#555555;stroke:white;} */
// /* .gauge  .tickline{stroke:black;stroke-width:25px;} */
// .gauge g.label text{text-anchor:middle;font-size:15px;font-weight:700;fill:#666; }
// </style>

'use strict';

class Gauge {
  constructor(configuration) {
    // default configuration settings
    // color: low=green, def=yellow, high=red
    const config = {
      size : 200,
      margin : 10,
      minValue : 0,
      maxValue : 10,
      majorTicks : 5,
      lowThreshhold : 3,
      highThreshhold : 7,
      scale: 'linear',
      lowThreshholdColor :  '#00C853',
      defaultColor :        '#ffe500',
      highThreshholdColor : '#EA4335',
      transitionMs : 1000,
      displayUnit: 'Value'
    };

    // define arc shape and position
    this.arcPadding = 20;
    this.arcWidth   = 30;
    this.labelInset = 12;

    this.minAngle = -90,
    this.maxAngle = 90,
    this.angleRange = this.maxAngle - this.minAngle;

    this.config = Object.assign(config, configuration);
    this._config();

  }

  _config() {

    // defined pointer shape and size
    const pointerWidth = 16;
    const pointerTailLength = 15;
    const pointerHeadLength = this._radius() - this.labelInset;
    this.lineData = [
        [pointerWidth / 2, 0],
        [0, -pointerHeadLength],
        [-(pointerWidth / 2), 0],
        [0, pointerTailLength],
        [pointerWidth / 2, 0]
      ];

    if (this.config.scale == 'log') {
      this.scale = d3.scaleLog()
        .range([0,1])
        .domain([this.config.minValue, this.config.maxValue]);
    }
    else {
      this.scale = d3.scaleLinear()
      .range([0,1])
      .domain([this.config.minValue, this.config.maxValue]);
    }

    const colorDomain = [this.config.lowThreshhold, this.config.highThreshhold].map(this.scale);
    const colorRange  = [
      this.config.lowThreshholdColor,
      this.config.defaultColor,
      this.config.highThreshholdColor
    ];
    this.colorScale = d3.scaleThreshold().domain(colorDomain).range(colorRange);

    let ticks = this.config.majorTicks;
    if (this.config.scale === 'log') {
      ticks = Math.log10(this.config.maxValue/this.config.minValue);
    }
    this.ticks = this.scale.ticks(ticks);

    this.threshholds = [
      this.config.minValue,
      this.config.lowThreshhold,
      this.config.highThreshhold,
      this.config.maxValue
    ]
    .map(d => this.scale(d));

    this.arc = d3.arc()
      .innerRadius(this._radius() - this.arcWidth - this.arcPadding)
      .outerRadius(this._radius() - this.arcPadding)
      .startAngle((d, i) => {
        const ratio = i > 0 ? this.threshholds[i-1] : this.threshholds[0];
        return this._deg2rad(this.minAngle + (ratio * this.angleRange));
      })
      .endAngle((d, i) => this._deg2rad(this.minAngle + this.threshholds[i] * this.angleRange));

  }

  _radius() {
    return (this.config.size - this.config.margin) / 2;
  }

  _deg2rad(deg) {
    return deg * Math.PI / 180;
  }

  setConfig(configuration) {
    this.config = Object.assign(this.config, configuration);
    this._config();
    return this;
  }

  render(container, newValue) {

  // clear gauge if exist
  d3.select(container).selectAll('svg').remove();
  d3.select(container).selectAll('div').remove();

  const svg = d3.select(container)
    .append('svg')
    .attr('class', 'gauge')
    .attr('width', this.config.size + this.config.margin)
    .attr('height', this.config.size / 2 + 1.3 * this.config.margin);

  // display panel arcs with color scale
  const arcs = svg.append('g')
    .attr('class', 'arc')
    .attr('transform', `translate(${this._radius()}, ${this._radius()})`);

  // draw the color arcs
  arcs.selectAll('path')
    .data(this.threshholds)
    .enter()
    .append('path')
    .attr('fill', d => this.colorScale(d-0.001))
    .attr('d', this.arc);

  // display panel - labels
  const lg = svg.append('g')
    .attr('class', 'label')
    .attr('transform', `translate(${this._radius()},${this._radius()})`);

  // display panel - text
  lg.selectAll('text')
    .data(this.ticks)
    .enter()
    .append('text')
    .attr('transform', d => {
       var newAngle = this.minAngle + (this.scale(d) * this.angleRange);
       return `rotate(${newAngle}) translate(0, ${this.labelInset - this._radius()})`;
     })
    .text(d3.format('1,.0f'));
    // .text(d3.format('1,.1f'));

  // display panel - ticks
  lg.selectAll('line')
    .data(this.ticks)
    .enter()
    .append('line')
    .attr('class', 'tickline')
    .attr('x1', 0)
    .attr('y1', 0)
    .attr('x2', 0)
    .attr('y2', this.arcWidth + this.labelInset)
    .attr('transform', d => {
      const newAngle = this.minAngle + (this.scale(d) * this.angleRange);
      return `rotate(${newAngle}), translate(0, ${this.arcWidth  - this.labelInset - this._radius()})`;
    })
    .style('stroke', '#666')
    .style('stroke-width', '1px');

  // display pointer
  const pg = svg.append('g')
    .data([this.lineData])
    .attr('class', 'pointer')
    .attr('transform', `translate(${this._radius()},${this._radius()})`);

  const pointer = pg.append('path')
    .attr('d', d3.line())
    .attr('transform', `rotate(${this.minAngle})`);

  // // display current value
  // const numberDiv = d3.select(container).append('div')
  //   .attr('class', 'number-div')
  //   .style('width', `${this.config.size - this.config.margin}px`);

  // const numberUnit = numberDiv.append('span')
  //   .attr('class', 'number-unit')
  //   .text(d => this.config.displayUnit);

  // const numberValue = numberDiv.append('span')
  //   .data([newValue])
  //   .attr('class', 'number-value')
  //   .text(d => d === undefined ? 0: d);

  this.pointer = pointer;
  // this.numberValue = numberValue;

  }

  update(newValue) {

    if (isNaN(newValue)) newValue = this.config.minValue; // added by ullix
    if (newValue < this.config.minValue) newValue = this.config.minValue; // if newValue is 0 at logScale, the pointer jumps to the middle

    const newAngle = this.minAngle + (this.scale(newValue) * this.angleRange);

    this.pointer.transition()
      .duration(this.config.transitionMs)
      .attr('transform', `rotate(${newAngle})`);

    // this.numberValue
    //   .data([newValue])
    //   .transition()
    //   .duration(this.config.transitionMs)
    //   .style('color', this.colorScale( this.scale(newValue) ))
    //   //.text(newValue.toFixed(3))
    //   .tween("", function(d) {
    //     const interpolator = d3.interpolate( this.textContent, d );
    //     const that = this;
    //     return function( t ) {
    //       that.textContent = interpolator(t).toFixed(1);
    //     };
    //   });
  }

}
