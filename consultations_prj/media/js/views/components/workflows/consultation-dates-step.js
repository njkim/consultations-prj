define([
    'jquery',
    'arches',
    'knockout',
    'knockout-mapping',
    'views/components/workflows/new-tile-step'
], function($, arches, ko, koMapping, NewTileStep) {
    function viewModel(params) {

        NewTileStep.apply(this, [params]);
        var self = this;

        if (!params.resourceid()) {
            params.resourceid(params.workflow.state.resourceid);
        }
        if (params.workflow.state.steps[params._index]) {
            params.tileid(params.workflow.state.steps[params._index].tileid);
        }

        var url = arches.urls.api_card + (ko.unwrap(params.resourceid) || ko.unwrap(params.graphid));


        params.tile = self.tile;
        this.relatedAppAreaTile = ko.observable();

        params.getStateProperties = function(){
            return {
                resourceid: ko.unwrap(params.resourceid),
                tile: !!(params.tile) ? koMapping.toJS(params.tile().data) : undefined,
                tileid: !!(params.tile) ? ko.unwrap(params.tile().tileid): undefined
            }
        };

        this.displayName = ko.observable();
        this.concatName = ko.observable('Consultation for [Application Area] on [Log Date]');
        this.consultationNameNodeId = '8d41e4ab-a250-11e9-87d1-00224800b26d';
        this.appAreaNodeId = "8d41e4de-a250-11e9-973b-00224800b26d";
        this.relatedAppAreaNodeId = '8d41e4ba-a250-11e9-9b20-00224800b26d';
        this.logDateNodeId = "8d41e4cf-a250-11e9-a86d-00224800b26d";
        this.targetDateNodeId = "8d41e4cb-a250-11e9-9cf2-00224800b26d";

        this.workflowStepClass = ko.unwrap(params.class());

        this.getResourceDisplayName = function(resourceids) {
            var retStr = '';
            resourceids.forEach(function(id) {
                $.get(
                    arches.urls.resource_descriptors + id,
                    function(descriptors) {
                        retStr == '' ? retStr = descriptors.displayname : retStr += (', '+descriptors.displayname);
                        self.displayName(retStr);
                    }
                );
            });
        };

        this.saveConsNameTile = function() {
            var nameCard = self.topCards.find(function(topCard) {
                return topCard.nodegroupid == self.consultationNameNodeId;
            });
            var nameCardTile = nameCard.getNewTile();
            nameCardTile.data[self.consultationNameNodeId](self.concatName());
            nameCardTile.save();
        };

        this.formatDate = function(date) {
            var formatted = date.getFullYear()+'-'+ ('0' + (date.getMonth()+1)).slice(-2)+'-'+('0' + date.getDate()).slice(-2);
            return formatted;
        };

        this.addDays = function(date, days) {
            var copy = new Date(Number(date));
            copy.setDate(date.getDate() + days);
            return self.formatDate(copy);
        };

        self.tile.subscribe(function(val) {
            var resourceids, logDateVal, targetDateVal;
            var DefaultTargetDateLeadTime = 22, relatedAppAreaTile = self.getTiles(self.relatedAppAreaNodeId)[0];
            if(!ko.unwrap(self.displayName) && !ko.unwrap(val.data[self.targetDateNodeId])) {
                resourceids = ko.unwrap(relatedAppAreaTile.data[self.appAreaNodeId]);
                self.getResourceDisplayName(resourceids);
            }
            if(val) {
                self.tile().data[self.logDateNodeId].subscribe(function(val) {
                    logDateVal = new Date(val);
                    if (logDateVal != 'Invalid Date') {
                        self.concatName('Consultation for '+self.displayName()+' on '+logDateVal.toLocaleDateString());
                        targetDateVal = self.addDays(logDateVal, DefaultTargetDateLeadTime);
                        self.tile().data[self.targetDateNodeId](targetDateVal);
                    }
                });
            }
        });

        self.onSaveSuccess = function(tiles) {
            var tile;
            self.saveConsNameTile();
            if (tiles.length > 0 || typeof tiles == 'object') {
                tile = tiles[0] || tiles;
                params.resourceid(tile.resourceinstance_id);
                params.tileid(tile.tileid);
                self.resourceId(tile.resourceinstance_id);
            }
            self.setStateProperties();
            params.workflow.updateUrl();
            if (self.completeOnSave === true) { self.complete(true); }
        };
    };

    return ko.components.register('consultation-dates-step', {
        viewModel: viewModel,
        template: {
            require: 'text!templates/views/components/workflows/hide-card-step.htm'
        }
    });
});
