
(function($) {
    var separator = "~";

    var numberList;
    var numberdiv;
    var quantity;

    getAllNumbers = function() {
        return numberList.value.split(separator);
    }

    updateQuantity = function(offset) {
        var oldQuantity = quantity.contents()[0].data;
        $(quantity).html(parseInt(oldQuantity)+offset);
    }

    deletedest = function(ev) {
        var div = $(ev.target.parentElement);
        var divContent = div.contents()[0].nodeValue;
        existing = getAllNumbers();
        for (n in existing) {
            if (existing[n] == divContent) {
                existing.splice(n, 1);
                updateQuantity(-1);
            }
        }
        div.empty();
        numberList.value = existing.join(separator);
    }

    addNumber = function(num) {
        existing = getAllNumbers();
        for (n in existing) {
            if(existing[n] == num) {
                return;
            }
        }

        if (numberList.value.length > 0)
            numberList.value += separator;
        numberList.value += num;
        numberdiv.append("<div>" + num + "<button class=\"nodest\">x</button></div>");
        $(".nodest").click(deletedest);
        updateQuantity(1);
    }

    clickNumber = function(ev) {
        addNumber(ev.target.value);
    }

    addFromText = function(ev) {
        var inputField = $("#destinationNumber")[0];
        addNumber(inputField.value);
        return false;
    }

    function PBHandlingInit() {
        numberList = $("#id_numberlist")[0];

        numberdiv = $("#recipientList");

        quantity = $("#recipientQuantity");

        $("#destinationFieldAdd").click(addFromText);
        $("#addFromList option").dblclick(clickNumber);
    }

    $(document).ready(function(){
     PBHandlingInit();
    });
})(django.jQuery);